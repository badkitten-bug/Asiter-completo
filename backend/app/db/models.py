"""
Modelos Pydantic para el backend.
"""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class TdrTipo(str, Enum):
    """Tipos de TDR según normativa peruana."""
    BIEN = "BIEN"
    OBRA = "OBRA"
    CONSULTORIA_OBRA = "CONSULTORIA_OBRA"
    SERVICIO = "SERVICIO"


class TdrDocument(BaseModel):
    """Documento TDR almacenado en la BD."""
    id: str
    filename: str
    category: str
    tipo: TdrTipo
    fields: dict[str, Any]
    text_for_embedding: str
    created_at: datetime = Field(default_factory=datetime.now)


class TdrSearchResult(BaseModel):
    """Resultado de búsqueda de TDR similar."""
    id: str
    filename: str
    tipo: TdrTipo
    similarity: float
    fields: dict[str, Any]


class GenerateFieldsRequest(BaseModel):
    """Request para generar campos de TDR."""
    tipo: TdrTipo
    descripcion_inicial: Optional[str] = None
    objeto_contratacion: Optional[str] = None
    campos_parciales: Optional[dict[str, str]] = None
    num_referencias: int = Field(default=5, ge=1, le=10)


class GenerateFieldsResponse(BaseModel):
    """Response con campos generados."""
    success: bool
    tipo: TdrTipo
    campos_sugeridos: dict[str, Any]
    referencias_usadas: list[TdrSearchResult]
    confidence: float


class SearchRequest(BaseModel):
    """Request para buscar TDRs similares."""
    query: str
    tipo: Optional[TdrTipo] = None
    limit: int = Field(default=5, ge=1, le=20)


class StatsResponse(BaseModel):
    """Estadísticas de la BD."""
    total_tdrs: int
    por_tipo: dict[str, int]
    por_categoria: dict[str, int]

