"""
Extractor de TDR usando Google Gemini API.

Gemini puede hacer OCR + extracción de campos en un solo paso,
lo que es mucho más rápido y preciso.
"""
import base64
import io
import json
import re
from pathlib import Path
from typing import Any, Optional

from google import genai
from google.genai import types
from PIL import Image

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


# Prompt del sistema para extracción de TDR
SYSTEM_PROMPT = """Actúa como un experto en contrataciones públicas del estado peruano.
Recibes imágenes de páginas de un TDR (Términos de Referencia) y debes extraer todos los campos detectables.

REGLAS IMPORTANTES:
1. NO inventes datos. Solo devuelve lo que exista EXPLÍCITAMENTE en el documento.
2. Si un campo no existe en el documento, NO lo incluyas en el JSON.
3. Mantén el texto original cuando sea posible.
4. Para listas (entregables, requisitos, etc.), usa arrays.
5. Para fechas y plazos, mantén el formato original del documento.

CAMPOS A DETECTAR (solo si existen):
- objeto_contratacion: Descripción del objeto de la contratación
- denominacion_servicio: Nombre del servicio o bien
- finalidad_publica: Para qué se necesita
- alcance: Alcance del servicio/bien
- servicios_requeridos: Lista de servicios o actividades
- entregables: Lista de entregables con plazos
- plazos: Información de plazos y duración
- lugar_prestacion: Dónde se realiza el servicio
- perfil_profesional: Requisitos del personal
- requisitos_tecnicos_minimos: Especificaciones técnicas
- penalidades: Penalidades por incumplimiento
- forma_pago: Condiciones de pago
- valor_referencial: Monto estimado
- supervision: Quién supervisa
- confidencialidad: Cláusulas de confidencialidad
- cualquier otro campo relevante que encuentres

Responde SOLO con un JSON válido, sin explicaciones adicionales ni markdown."""


class GeminiExtractor:
    """Extractor de TDR usando Google Gemini."""
    
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"  # Modelo rápido con visión
    
    def pdf_to_images(self, pdf_path: str, dpi: int = 150, max_pages: int = 50) -> list[Image.Image]:
        """Convierte PDF a lista de imágenes."""
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF no está instalado. Ejecuta: pip install PyMuPDF")
        
        images = []
        pdf_document = fitz.open(pdf_path)
        
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        
        total_pages = min(pdf_document.page_count, max_pages)
        
        for page_num in range(total_pages):
            page = pdf_document[page_num]
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            img_data = pixmap.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
        
        pdf_document.close()
        return images
    
    def image_to_base64(self, image: Image.Image) -> bytes:
        """Convierte imagen PIL a bytes."""
        buffer = io.BytesIO()
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        image.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()
    
    async def extract_from_pdf(self, pdf_path: str, max_pages: int = 30) -> dict[str, Any]:
        """
        Extrae campos de un PDF usando Gemini Vision.
        
        Args:
            pdf_path: Ruta al archivo PDF
            max_pages: Máximo de páginas a procesar
            
        Returns:
            dict con los campos extraídos
        """
        # Convertir PDF a imágenes
        images = self.pdf_to_images(pdf_path, dpi=120, max_pages=max_pages)
        
        if not images:
            return {"error": "No se pudieron extraer imágenes del PDF"}
        
        # Preparar contenido para Gemini
        contents = [SYSTEM_PROMPT]
        
        # Agregar cada imagen
        for i, img in enumerate(images):
            img_bytes = self.image_to_base64(img)
            contents.append(
                types.Part.from_bytes(
                    data=img_bytes,
                    mime_type="image/jpeg"
                )
            )
            contents.append(f"[Página {i+1} de {len(images)}]")
        
        contents.append("Analiza todas las páginas del TDR y extrae los campos en formato JSON.")
        
        # Llamar a Gemini
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=8192,
            )
        )
        
        # Parsear respuesta JSON
        return self._parse_json_response(response.text)
    
    def extract_from_pdf_sync(self, pdf_path: str, max_pages: int = 30) -> dict[str, Any]:
        """Versión síncrona de extract_from_pdf."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.extract_from_pdf(pdf_path, max_pages)
        )
    
    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """Parsea la respuesta del LLM que debería ser JSON."""
        # Limpiar posibles marcadores de código
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
            # Intentar extraer JSON del texto
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            return {"raw_response": content, "parse_error": True}


# Función de conveniencia para uso directo
def extract_tdr_with_gemini(pdf_path: str, api_key: str, max_pages: int = 30) -> dict[str, Any]:
    """
    Extrae campos de un TDR usando Gemini.
    
    Args:
        pdf_path: Ruta al PDF
        api_key: API key de Google
        max_pages: Máximo de páginas
        
    Returns:
        dict con campos extraídos
    """
    extractor = GeminiExtractor(api_key)
    return extractor.extract_from_pdf_sync(pdf_path, max_pages)

