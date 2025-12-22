"""
Módulo de OCR para extracción de texto desde PDFs.

Soporta:
- PDFs digitales (texto embebido)
- PDFs escaneados (imágenes con OCR)
- Detección automática del tipo de PDF
"""
import io
import os
import tempfile
from pathlib import Path
from typing import Optional

from PIL import Image
from pypdf import PdfReader

from .config import get_settings

# Intentar importar pdf2image y pytesseract (opcionales para OCR de imágenes)
try:
    from pdf2image import convert_from_path, convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import pytesseract
    # Verificar si tesseract está realmente instalado en el sistema
    try:
        pytesseract.get_tesseract_version()
        TESSERACT_AVAILABLE = True
    except Exception:
        TESSERACT_AVAILABLE = False
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None


class OCRProcessor:
    """Procesador de OCR para PDFs."""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Configurar Tesseract si está disponible
        if TESSERACT_AVAILABLE and self.settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.settings.tesseract_cmd
    
    def extract_text_from_pdf(self, pdf_path: str | Path) -> dict:
        """
        Extrae texto de un PDF, usando OCR si es necesario.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            dict con:
                - text: Texto completo extraído
                - pages: Lista de textos por página
                - method: 'digital' o 'ocr'
                - page_count: Número de páginas
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")
        
        # Primero intentar extracción digital
        result = self._extract_digital_text(pdf_path)
        
        # Si hay muy poco texto, probablemente es escaneado
        if self._is_scanned_pdf(result["text"], result["page_count"]):
            if PDF2IMAGE_AVAILABLE and TESSERACT_AVAILABLE:
                result = self._extract_ocr_text(pdf_path)
            else:
                result["warning"] = "PDF parece ser escaneado pero OCR no está disponible"
        
        return result
    
    def extract_text_from_bytes(self, pdf_bytes: bytes) -> dict:
        """
        Extrae texto de un PDF en bytes.
        
        Args:
            pdf_bytes: Contenido del PDF en bytes
            
        Returns:
            dict con texto extraído y metadatos
        """
        # Guardar temporalmente para procesar
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name
        
        try:
            return self.extract_text_from_pdf(tmp_path)
        finally:
            # Limpiar archivo temporal
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def _extract_digital_text(self, pdf_path: Path) -> dict:
        """Extrae texto de un PDF digital (texto embebido)."""
        reader = PdfReader(pdf_path)
        pages_text = []
        
        for page in reader.pages[:self.settings.max_pages]:
            text = page.extract_text() or ""
            pages_text.append(text)
        
        full_text = "\n\n--- PÁGINA {} ---\n\n".join(
            [f"{i+1}" for i in range(len(pages_text))]
        )
        
        # Construir texto con separadores de página
        full_text = ""
        for i, text in enumerate(pages_text):
            if text.strip():
                full_text += f"\n\n--- PÁGINA {i+1} ---\n\n{text}"
        
        return {
            "text": full_text.strip(),
            "pages": pages_text,
            "method": "digital",
            "page_count": len(reader.pages),
        }
    
    def _extract_ocr_text(self, pdf_path: Path) -> dict:
        """Extrae texto usando OCR (para PDFs escaneados)."""
        if not PDF2IMAGE_AVAILABLE:
            raise RuntimeError("pdf2image no está instalado")
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("pytesseract no está instalado")
        
        # Convertir PDF a imágenes
        images = convert_from_path(
            pdf_path,
            dpi=300,
            first_page=1,
            last_page=self.settings.max_pages,
        )
        
        pages_text = []
        for i, image in enumerate(images):
            # Aplicar OCR a cada página
            text = pytesseract.image_to_string(
                image,
                lang=self.settings.ocr_language,
            )
            pages_text.append(text)
        
        # Construir texto completo
        full_text = ""
        for i, text in enumerate(pages_text):
            if text.strip():
                full_text += f"\n\n--- PÁGINA {i+1} ---\n\n{text}"
        
        return {
            "text": full_text.strip(),
            "pages": pages_text,
            "method": "ocr",
            "page_count": len(images),
        }
    
    def _is_scanned_pdf(self, text: str, page_count: int) -> bool:
        """
        Determina si un PDF es probablemente escaneado.
        
        Un PDF escaneado típicamente tiene muy poco o ningún texto extraíble.
        """
        if not text:
            return True
        
        # Promedio de caracteres por página
        chars_per_page = len(text) / max(page_count, 1)
        
        # Si hay menos de 100 caracteres por página, probablemente es escaneado
        return chars_per_page < 100


# Instancia global del procesador
ocr_processor = OCRProcessor()


def extract_text(pdf_path: str | Path) -> dict:
    """Función de conveniencia para extraer texto."""
    return ocr_processor.extract_text_from_pdf(pdf_path)


def extract_text_from_bytes(pdf_bytes: bytes) -> dict:
    """Función de conveniencia para extraer texto desde bytes."""
    return ocr_processor.extract_text_from_bytes(pdf_bytes)

