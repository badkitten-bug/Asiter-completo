"""
Módulo para OCR usando DeepSeek Vision API.

Este módulo convierte PDFs a imágenes y las envía a la API de DeepSeek
para obtener el texto extraído con alta precisión.
"""
import base64
import io
import os
from pathlib import Path
from typing import List, Optional, Tuple

import httpx
from PIL import Image

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

from .config import get_settings


class DeepSeekOCRClient:
    """Cliente para DeepSeek Vision API con capacidad OCR."""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.deepseek_api_key
        self.base_url = self.settings.deepseek_base_url
        
        # Prompt optimizado para OCR de documentos TDR peruanos
        self.ocr_prompt = """Actúa como un sistema OCR de alta precisión para documentos gubernamentales peruanos.

Tu tarea es extraer TODO el texto visible en esta imagen de un documento TDR (Términos de Referencia).

INSTRUCCIONES:
1. Extrae el texto exactamente como aparece en el documento
2. Mantén la estructura: títulos, subtítulos, párrafos, listas, tablas
3. Para tablas, usa formato markdown
4. NO interpretes ni resumas - solo transcribe
5. Si hay números, fechas o montos, transcríbelos exactamente
6. Incluye encabezados y pies de página si existen

Devuelve SOLO el texto extraído, sin comentarios adicionales."""

    def image_to_base64(self, image: Image.Image, format: str = "JPEG") -> str:
        """Convierte imagen PIL a base64."""
        buffer = io.BytesIO()
        # Convertir a RGB si es necesario
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        image.save(buffer, format=format, quality=95)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def pdf_to_images(self, pdf_path: str, dpi: int = 150) -> List[Image.Image]:
        """Convierte PDF a lista de imágenes usando PyMuPDF."""
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF (fitz) no está instalado. Ejecuta: pip install PyMuPDF")
        
        images = []
        pdf_document = fitz.open(pdf_path)
        
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            
            # Convertir a PIL Image
            img_data = pixmap.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
        
        pdf_document.close()
        return images

    def pdf_bytes_to_images(self, pdf_bytes: bytes, dpi: int = 150) -> List[Image.Image]:
        """Convierte bytes de PDF a lista de imágenes."""
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF (fitz) no está instalado. Ejecuta: pip install PyMuPDF")
        
        images = []
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            
            img_data = pixmap.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
        
        pdf_document.close()
        return images

    async def ocr_image(self, image: Image.Image, custom_prompt: Optional[str] = None) -> str:
        """Envía una imagen a DeepSeek Vision API para OCR."""
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY no está configurada")
        
        # Redimensionar si es muy grande (optimización de costos)
        max_size = 2048
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        image_base64 = self.image_to_base64(image)
        prompt = custom_prompt or self.ocr_prompt
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",  # DeepSeek chat tiene capacidad de visión
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_base64}"
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.0
                }
            )
            
            if response.status_code != 200:
                error_detail = response.text
                raise Exception(f"Error en DeepSeek API: {response.status_code} - {error_detail}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"]

    async def ocr_pdf(
        self, 
        pdf_path: str, 
        dpi: int = 150,
        progress_callback: Optional[callable] = None
    ) -> Tuple[str, int]:
        """
        Procesa un PDF completo y devuelve el texto extraído.
        
        Returns:
            Tuple[str, int]: (texto_completo, numero_de_paginas)
        """
        images = self.pdf_to_images(pdf_path, dpi)
        all_text = []
        
        for i, image in enumerate(images):
            if progress_callback:
                progress_callback(i + 1, len(images))
            
            page_text = await self.ocr_image(image)
            all_text.append(f"--- Página {i + 1} ---\n{page_text}")
        
        return "\n\n".join(all_text), len(images)

    async def ocr_pdf_bytes(
        self, 
        pdf_bytes: bytes, 
        dpi: int = 150,
        progress_callback: Optional[callable] = None
    ) -> Tuple[str, int]:
        """
        Procesa bytes de PDF y devuelve el texto extraído.
        """
        images = self.pdf_bytes_to_images(pdf_bytes, dpi)
        all_text = []
        
        for i, image in enumerate(images):
            if progress_callback:
                progress_callback(i + 1, len(images))
            
            page_text = await self.ocr_image(image)
            all_text.append(f"--- Página {i + 1} ---\n{page_text}")
        
        return "\n\n".join(all_text), len(images)


# Función de conveniencia
async def extract_text_with_deepseek(
    pdf_path: str = None,
    pdf_bytes: bytes = None,
    dpi: int = 150
) -> Tuple[str, int]:
    """
    Extrae texto de un PDF usando DeepSeek Vision API.
    
    Args:
        pdf_path: Ruta al archivo PDF
        pdf_bytes: Bytes del PDF (alternativa a pdf_path)
        dpi: Resolución para la conversión (default 150)
    
    Returns:
        Tuple[str, int]: (texto_extraído, número_de_páginas)
    """
    client = DeepSeekOCRClient()
    
    if pdf_bytes:
        return await client.ocr_pdf_bytes(pdf_bytes, dpi)
    elif pdf_path:
        return await client.ocr_pdf(pdf_path, dpi)
    else:
        raise ValueError("Debe proporcionar pdf_path o pdf_bytes")

