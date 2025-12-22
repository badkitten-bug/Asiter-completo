"""
Servicio RAG para generación de campos de TDR.
"""
import json
from typing import Any, Optional

from google import genai
from google.genai import types

from ..config import get_settings
from ..db.chroma import chroma_client
from ..db.models import TdrTipo, TdrSearchResult, GenerateFieldsResponse
from .embeddings import embedding_service


# Mapeo de tipos de TDR a categorías de JSONs
TIPO_TO_CATEGORY = {
    TdrTipo.BIEN: "Bien",
    TdrTipo.SERVICIO: "Servicio",
    TdrTipo.CONSULTORIA_OBRA: "Consultoria de obra",
    TdrTipo.OBRA: "Obra"
}


class RAGService:
    """Servicio RAG para generar campos de TDR."""
    
    def __init__(self):
        settings = get_settings()
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model
    
    def search_similar_tdrs(
        self,
        query: str,
        tipo: Optional[TdrTipo] = None,
        limit: int = 5
    ) -> list[TdrSearchResult]:
        """Busca TDRs similares en la BD vectorial."""
        # Generar embedding de la query
        query_embedding = embedding_service.get_embedding(query)
        
        # Buscar en ChromaDB
        return chroma_client.search(
            query_embedding=query_embedding,
            n_results=limit,
            tipo=tipo
        )
    
    def generate_fields(
        self,
        tipo: TdrTipo,
        descripcion_inicial: Optional[str] = None,
        objeto_contratacion: Optional[str] = None,
        campos_parciales: Optional[dict[str, str]] = None,
        num_referencias: int = 5
    ) -> GenerateFieldsResponse:
        """
        Genera campos de TDR usando RAG.
        
        1. Busca TDRs similares en la BD
        2. Usa los campos de esos TDRs como contexto
        3. Genera campos sugeridos con Gemini
        """
        # Construir query de búsqueda
        query_parts = [f"Tipo: {tipo.value}"]
        if descripcion_inicial:
            query_parts.append(descripcion_inicial)
        if objeto_contratacion:
            query_parts.append(objeto_contratacion)
        if campos_parciales:
            for k, v in campos_parciales.items():
                query_parts.append(f"{k}: {v}")
        
        query = "\n".join(query_parts)
        
        # Buscar TDRs similares
        referencias = self.search_similar_tdrs(query, tipo, num_referencias)
        
        if not referencias:
            # No hay referencias, generar desde cero
            return self._generate_without_context(tipo, descripcion_inicial, objeto_contratacion)
        
        # Construir contexto con las referencias
        contexto = self._build_context(referencias)
        
        # Generar campos con Gemini
        campos_sugeridos = self._generate_with_gemini(
            tipo=tipo,
            contexto=contexto,
            descripcion_inicial=descripcion_inicial,
            objeto_contratacion=objeto_contratacion,
            campos_parciales=campos_parciales
        )
        
        # Calcular confianza basada en similaridad promedio
        avg_similarity = sum(r.similarity for r in referencias) / len(referencias)
        
        return GenerateFieldsResponse(
            success=True,
            tipo=tipo,
            campos_sugeridos=campos_sugeridos,
            referencias_usadas=referencias,
            confidence=avg_similarity
        )
    
    def _build_context(self, referencias: list[TdrSearchResult]) -> str:
        """Construye el contexto a partir de las referencias."""
        context_parts = []
        
        for i, ref in enumerate(referencias, 1):
            context_parts.append(f"=== REFERENCIA {i} (Similaridad: {ref.similarity:.2f}) ===")
            context_parts.append(f"Archivo: {ref.filename}")
            context_parts.append(f"Tipo: {ref.tipo.value}")
            
            # Agregar campos relevantes
            for key, value in list(ref.fields.items())[:15]:
                if value:
                    if isinstance(value, (list, dict)):
                        value_str = json.dumps(value, ensure_ascii=False)[:500]
                    else:
                        value_str = str(value)[:500]
                    context_parts.append(f"  {key}: {value_str}")
            
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _generate_with_gemini(
        self,
        tipo: TdrTipo,
        contexto: str,
        descripcion_inicial: Optional[str],
        objeto_contratacion: Optional[str],
        campos_parciales: Optional[dict[str, str]]
    ) -> dict[str, Any]:
        """Genera campos usando Gemini con contexto RAG."""
        
        # Campos específicos según tipo de TDR
        campos_por_tipo = {
            TdrTipo.BIEN: """
  "denominacion_contratacion": "Nombre completo de la contratación",
  "finalidad_publica": "Para qué se necesita este bien, beneficio a la ciudadanía",
  "objetivo_general": "Objetivo principal de la contratación",
  "objetivos_especificos": "Lista de objetivos específicos separados por punto y coma",
  "alcance_descripcion_bienes": "Descripción detallada del bien a adquirir",
  "caracteristicas": "Características físicas y funcionales del bien",
  "caracteristicas_tecnicas": "Especificaciones técnicas detalladas",
  "cantidad": "Cantidad a adquirir (número)",
  "unidad_medida": "Unidad de medida (unidad, caja, etc.)",
  "perfil_proveedor": "Requisitos que debe cumplir el proveedor",
  "requisitos_proveedor": "Lista de documentos y requisitos",
  "plazo": "Plazo de entrega en días calendario",
  "lugar": "Lugar de entrega del bien",
  "forma_pago": "Condiciones de pago",
  "garantia_comercial": "Periodo de garantía del bien",
  "penalidades": "Penalidades por incumplimiento",
  "anticorrupcion_antisoborno": "Cláusula estándar anticorrupción",
  "conformidad": "Quién otorga la conformidad",
  "antecedentes": "Contexto y antecedentes de la necesidad"
""",
            TdrTipo.SERVICIO: """
  "denominacion_contratacion": "Nombre completo del servicio",
  "finalidad_publica": "Para qué se necesita este servicio, beneficio a la ciudadanía",
  "objetivo_contratacion": "Objetivo principal de la contratación",
  "objetivo_general": "Objetivo general del servicio",
  "objetivos_especificos": "Lista de objetivos específicos",
  "alcance_descripcion_servicio": "Descripción detallada del servicio",
  "actividades": "Lista de actividades a realizar",
  "entregables": "Lista de entregables con plazos",
  "perfil_proveedor": "Perfil profesional requerido (formación, experiencia, conocimientos)",
  "requisitos_proveedor": "Requisitos documentarios del proveedor",
  "formacion_academica": "Formación académica requerida",
  "experiencia": "Experiencia laboral requerida",
  "plazo": "Plazo de ejecución del servicio",
  "lugar": "Lugar de prestación del servicio",
  "forma_pago": "Condiciones y forma de pago",
  "penalidades": "Penalidades por incumplimiento",
  "confidencialidad": "Cláusula de confidencialidad",
  "anticorrupcion_antisoborno": "Cláusula estándar anticorrupción",
  "conformidad": "Quién otorga la conformidad",
  "antecedentes": "Contexto y antecedentes de la necesidad"
""",
            TdrTipo.CONSULTORIA_OBRA: """
  "denominacion_contratacion": "Nombre de la consultoría",
  "finalidad_publica": "Beneficio público de la consultoría",
  "objetivo_contratacion": "Objetivo de la contratación",
  "objetivo_general": "Objetivo general",
  "objetivos_especificos": "Objetivos específicos",
  "alcance_servicio": "Alcance de la consultoría",
  "descripcion_detallada_servicio": "Descripción detallada",
  "actividades": "Actividades de la consultoría",
  "plan_trabajo": "Plan de trabajo propuesto",
  "supervision": "Supervisión del servicio",
  "funciones_especificas": "Funciones del consultor",
  "perfil_proveedor": "Perfil profesional requerido",
  "plazo": "Plazo de ejecución",
  "conformidad": "Otorgamiento de conformidad",
  "penalidades": "Penalidades aplicables",
  "costo_total": "Costo total de la consultoría"
""",
            TdrTipo.OBRA: """
  "denominacion_contratacion": "Nombre de la obra",
  "descripcion": "Descripción de la obra",
  "cantidad": "Cantidad o metraje",
  "unidad_medida": "Unidad de medida",
  "valor_unitario": "Valor unitario",
  "importe_total": "Importe total"
"""
        }
        
        campos_tipo = campos_por_tipo.get(tipo, campos_por_tipo[TdrTipo.SERVICIO])
        
        prompt = f"""Eres un experto en contrataciones públicas del estado peruano.

Tu tarea es generar TODOS los campos para un nuevo TDR (Términos de Referencia) de tipo "{tipo.value}".

CONTEXTO - TDRs similares como referencia:
{contexto}

INFORMACIÓN DEL NUEVO TDR:
- Tipo: {tipo.value}
- Descripción inicial: {descripcion_inicial or 'No proporcionada'}
- Objeto de contratación: {objeto_contratacion or 'No proporcionado'}
- Campos ya completados: {json.dumps(campos_parciales, ensure_ascii=False) if campos_parciales else 'Ninguno'}

INSTRUCCIONES IMPORTANTES:
1. GENERA TODOS los campos listados abajo - no dejes ninguno vacío
2. Basándote en los TDRs de referencia, crea contenido coherente y profesional
3. Usa lenguaje formal propio de documentos gubernamentales peruanos
4. Para campos legales (anticorrupción, confidencialidad), usa textos estándar del estado peruano
5. Adapta todo al contexto específico del objeto de contratación
6. Sé específico y detallado, evita frases genéricas

CAMPOS A GENERAR (todos obligatorios):
{{
{campos_tipo}
}}

TEXTOS ESTÁNDAR A USAR:
- Para "anticorrupcion_antisoborno": "El contratista declara y garantiza no haber ofrecido, negociado o efectuado cualquier pago, objeto de valor o cualquier dádiva en general a funcionarios públicos. Se compromete a conducirse en todo momento con honestidad, probidad, veracidad e integridad, así como no incurrir en prácticas de corrupción, soborno o cualquier tipo de acto contrario a la ética."
- Para "confidencialidad": "El contratista se obliga a mantener en reserva y confidencialidad la información a la que tenga acceso en razón del servicio contratado. Queda prohibido revelar, publicar, difundir o usar esta información sin autorización expresa de la Entidad, durante y después de la vigencia del contrato."

Responde SOLO con el JSON válido, sin explicaciones ni markdown."""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=4096,
            )
        )
        
        # Parsear respuesta JSON
        return self._parse_json_response(response.text)
    
    def _generate_without_context(
        self,
        tipo: TdrTipo,
        descripcion_inicial: Optional[str],
        objeto_contratacion: Optional[str]
    ) -> GenerateFieldsResponse:
        """Genera campos sin contexto de referencia."""
        prompt = f"""Genera campos para un TDR de tipo "{tipo.value}" con la siguiente información:
- Descripción: {descripcion_inicial or 'No proporcionada'}
- Objeto: {objeto_contratacion or 'No proporcionado'}

Responde con un JSON de campos típicos para este tipo de TDR."""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.5,
                max_output_tokens=4096,
            )
        )
        
        campos = self._parse_json_response(response.text)
        
        return GenerateFieldsResponse(
            success=True,
            tipo=tipo,
            campos_sugeridos=campos,
            referencias_usadas=[],
            confidence=0.3  # Baja confianza sin referencias
        )
    
    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """Parsea respuesta JSON de Gemini."""
        import re
        
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            return {"error": "No se pudo parsear la respuesta", "raw": content[:500]}


# Instancia global
rag_service = RAGService()

