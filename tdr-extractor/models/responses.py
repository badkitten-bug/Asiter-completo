"""
Modelos Pydantic para las respuestas del API.

NOTA: Los campos extraídos del TDR son flexibles y no tienen esquema fijo.
Estos modelos son solo para las respuestas estructuradas del API.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Respuesta del health check."""
    status: str
    timestamp: datetime
    config: dict[str, Any]


class ExtractionMetadata(BaseModel):
    """Metadatos de la extracción."""
    processed_at: datetime
    saved_path: Optional[str] = None
    text_length: int


class ExtractionResponse(BaseModel):
    """Respuesta de la extracción de TDR."""
    success: bool
    filename: str
    extraction_method: str = Field(description="'digital' o 'ocr'")
    page_count: int
    fields: dict[str, Any] = Field(
        description="Campos extraídos del TDR (esquema flexible)"
    )
    metadata: ExtractionMetadata
    warning: Optional[str] = None
    error: Optional[str] = None


class TextExtractionResponse(BaseModel):
    """Respuesta de la extracción de solo texto."""
    success: bool
    filename: str
    method: str
    page_count: int
    text: str
    pages: list[str]


class ErrorResponse(BaseModel):
    """Respuesta de error."""
    success: bool = False
    error: str
    detail: Optional[str] = None

