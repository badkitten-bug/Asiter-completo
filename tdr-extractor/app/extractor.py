"""
Módulo extractor que llama al LLM para extraer campos del TDR.

Soporta:
- DeepSeek API (remoto)
- Ollama (local)
- LLama-cpp (local, opcional)
"""
import json
import re
from typing import Any, Optional

import httpx

from .config import get_settings

# Prompt del sistema para extracción de TDR
SYSTEM_PROMPT = """Actúa como un experto en contrataciones públicas del estado peruano.
Recibe el texto completo de un TDR (Términos de Referencia) y devuelve un JSON con todos los campos detectables.

REGLAS IMPORTANTES:
1. NO inventes datos. Solo devuelve lo que exista EXPLÍCITAMENTE en el documento.
2. Si un campo no existe en el documento, NO lo incluyas en el JSON.
3. Mantén el texto original cuando sea posible.
4. Para listas (entregables, requisitos, etc.), usa arrays.
5. Para fechas y plazos, mantén el formato original del documento.

CAMPOS A DETECTAR (solo si existen):
- objeto_contratacion: Descripción del objeto de la contratación
- denominacion_servicio: Nombre del servicio
- finalidad_publica: Finalidad pública de la contratación
- alcance: Alcance del servicio
- servicios_requeridos: Lista de servicios específicos requeridos
- actividades: Actividades a realizar
- entregables: Lista de entregables con sus plazos
- plazos: Información de plazos de ejecución
- plazo_ejecucion: Plazo total de ejecución
- lugar_prestacion: Lugar de prestación del servicio
- perfil_profesional: Requisitos del perfil profesional
- experiencia_requerida: Experiencia mínima requerida
- formacion_academica: Formación académica requerida
- requisitos_tecnicos_minimos: Lista de requisitos técnicos mínimos
- equipamiento: Equipamiento requerido
- penalidades: Penalidades por incumplimiento
- forma_pago: Forma de pago
- monto_referencial: Monto referencial o presupuesto
- garantias: Garantías requeridas
- coordinacion_supervision: Área de coordinación y supervisión
- confidencialidad: Cláusulas de confidencialidad
- propiedad_intelectual: Términos de propiedad intelectual
- normativa_aplicable: Normativa legal aplicable
- otras_condiciones: Otras condiciones relevantes
- anexos: Anexos mencionados

FORMATO DE RESPUESTA:
Responde ÚNICAMENTE con un JSON válido, sin texto adicional antes o después.
El JSON debe ser flexible: incluye solo los campos que encuentres en el documento.

Ejemplo de estructura (los campos varían según el documento):
{
  "objeto_contratacion": "...",
  "plazo_ejecucion": "...",
  "entregables": [
    {"nombre": "...", "plazo": "..."},
    ...
  ],
  "perfil_profesional": {
    "formacion": "...",
    "experiencia": "..."
  }
}"""


class LLMExtractor:
    """Extractor de campos usando LLM."""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def extract_fields(self, text: str) -> dict[str, Any]:
        """
        Extrae campos del TDR usando el LLM configurado.
        
        Args:
            text: Texto completo del TDR
            
        Returns:
            dict con los campos extraídos
        """
        if self.settings.use_local_llm:
            return await self._extract_with_ollama(text)
        else:
            return await self._extract_with_deepseek(text)
    
    async def _extract_with_ollama(self, text: str) -> dict[str, Any]:
        """Extrae campos usando Ollama (modelo local)."""
        url = f"{self.settings.ollama_base_url}/api/chat"
        
        # Truncar texto si es muy largo (Ollama tiene límites de contexto)
        max_chars = 25000  # ~6000 tokens aproximadamente
        if len(text) > max_chars:
            # Mantener inicio y final del documento (donde suelen estar los datos importantes)
            half = max_chars // 2
            text = text[:half] + "\n\n[... contenido truncado ...]\n\n" + text[-half:]
        
        payload = {
            "model": self.settings.ollama_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analiza el siguiente TDR y extrae todos los campos detectables:\n\n{text}"}
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,  # Baja temperatura para respuestas más determinísticas
                "num_ctx": 16384,    # Contexto para documentos
            }
        }
        
        async with httpx.AsyncClient(timeout=600.0) as client:  # 10 minutos timeout
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result.get("message", {}).get("content", "{}")
            
            return self._parse_json_response(content)
    
    async def _extract_with_deepseek(self, text: str) -> dict[str, Any]:
        """Extrae campos usando DeepSeek API."""
        url = f"{self.settings.deepseek_base_url}/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.settings.deepseek_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analiza el siguiente TDR y extrae todos los campos detectables:\n\n{text}"}
            ],
            "temperature": 0.1,
            "max_tokens": 8192,
            "response_format": {"type": "json_object"},
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            return self._parse_json_response(content)
    
    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """
        Parsea la respuesta JSON del LLM.
        
        Maneja casos donde el LLM incluye texto adicional.
        """
        content = content.strip()
        
        # Intentar parsear directamente
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Buscar JSON en bloques de código
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Buscar el primer { y último }
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(content[start:end+1])
            except json.JSONDecodeError:
                pass
        
        # Si todo falla, devolver el contenido como texto
        return {
            "raw_response": content,
            "error": "No se pudo parsear la respuesta como JSON"
        }


# Instancia global del extractor
llm_extractor = LLMExtractor()


async def extract_tdr_fields(text: str) -> dict[str, Any]:
    """Función de conveniencia para extraer campos del TDR."""
    return await llm_extractor.extract_fields(text)

