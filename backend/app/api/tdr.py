"""
Endpoints de TDR para el frontend.
"""
import json
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.chroma import chroma_client
from ..db.postgres import get_db
from ..db.sql_models import TdrGenerado, User
from ..db.models import (
    TdrTipo,
    GenerateFieldsRequest,
    GenerateFieldsResponse,
    SearchRequest,
    TdrSearchResult,
    StatsResponse
)
from ..services.rag import rag_service
from ..services.embeddings import embedding_service
from ..dependencies import get_current_user, require_auth

router = APIRouter(prefix="/api/tdr", tags=["TDR"])


class AddTdrRequest(BaseModel):
    """Request para agregar un nuevo TDR a la base de datos."""
    tipo: TdrTipo
    titulo: str
    campos: dict[str, Any]
    usuario: Optional[str] = None


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Obtiene estadísticas de la base de datos de TDRs."""
    stats = chroma_client.get_stats()
    return StatsResponse(**stats)


@router.post("/search", response_model=list[TdrSearchResult])
async def search_tdrs(request: SearchRequest):
    """
    Busca TDRs similares en la base de datos.
    
    - **query**: Texto de búsqueda
    - **tipo**: Filtrar por tipo de TDR (opcional)
    - **limit**: Número máximo de resultados
    """
    results = rag_service.search_similar_tdrs(
        query=request.query,
        tipo=request.tipo,
        limit=request.limit
    )
    return results


@router.get("/search", response_model=list[TdrSearchResult])
async def search_tdrs_get(
    q: str = Query(..., description="Texto de búsqueda"),
    tipo: Optional[TdrTipo] = Query(None, description="Tipo de TDR"),
    limit: int = Query(5, ge=1, le=20, description="Número de resultados")
):
    """Busca TDRs similares (versión GET)."""
    results = rag_service.search_similar_tdrs(
        query=q,
        tipo=tipo,
        limit=limit
    )
    return results


@router.post("/generate", response_model=GenerateFieldsResponse)
async def generate_fields(request: GenerateFieldsRequest):
    """
    Genera campos para un nuevo TDR usando RAG.
    
    - **tipo**: Tipo de TDR (BIEN, SERVICIO, OBRA, CONSULTORIA_OBRA)
    - **descripcion_inicial**: Descripción del servicio/bien a contratar
    - **objeto_contratacion**: Objeto de la contratación
    - **campos_parciales**: Campos ya completados por el usuario
    - **num_referencias**: Número de TDRs de referencia a usar
    """
    try:
        response = rag_service.generate_fields(
            tipo=request.tipo,
            descripcion_inicial=request.descripcion_inicial,
            objeto_contratacion=request.objeto_contratacion,
            campos_parciales=request.campos_parciales,
            num_referencias=request.num_referencias
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tipos")
async def get_tipos():
    """Obtiene los tipos de TDR disponibles."""
    return {
        "tipos": [
            {"value": "BIEN", "label": "Bien", "description": "Contratación de bienes materiales"},
            {"value": "SERVICIO", "label": "Servicio", "description": "Contratación de servicios profesionales"},
            {"value": "CONSULTORIA_OBRA", "label": "Consultoría de Obra", "description": "Servicios de consultoría para obras"},
            {"value": "OBRA", "label": "Obra", "description": "Contratación de obras de construcción"}
        ]
    }


@router.get("/my-tdrs")
async def get_my_tdrs(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Obtiene los TDRs generados por el usuario actual.
    """
    try:
        # Consultar TDRs del usuario
        tdrs = db.query(TdrGenerado)\
            .filter(TdrGenerado.user_id == current_user.id)\
            .order_by(TdrGenerado.created_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()
        
        # Contar total
        total = db.query(TdrGenerado)\
            .filter(TdrGenerado.user_id == current_user.id)\
            .count()
        
        return {
            "tdrs": [
                {
                    "id": tdr.id,
                    "tipo": tdr.tipo,
                    "titulo": tdr.titulo,
                    "created_at": tdr.created_at.isoformat(),
                    "updated_at": tdr.updated_at.isoformat(),
                    "campos": tdr.datos_json
                }
                for tdr in tdrs
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener TDRs: {str(e)}"
        )


@router.get("/{tdr_id}")
async def get_tdr(tdr_id: str):
    """Obtiene un TDR por su ID."""
    # Buscar en ChromaDB
    result = chroma_client.collection.get(ids=[tdr_id], include=["metadatas", "documents"])
    
    if not result["ids"]:
        raise HTTPException(status_code=404, detail="TDR no encontrado")
    
    metadata = result["metadatas"][0] if result["metadatas"] else {}
    document = result["documents"][0] if result["documents"] else ""
    
    # Parsear fields
    fields = {}
    if "fields_json" in metadata:
        try:
            fields = json.loads(metadata["fields_json"])
        except json.JSONDecodeError:
            pass
    
    return {
        "id": tdr_id,
        "filename": metadata.get("filename", ""),
        "tipo": metadata.get("tipo", ""),
        "category": metadata.get("category", ""),
        "fields": fields,
        "document": document
    }


@router.post("/add")
async def add_tdr(
    request: AddTdrRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Agrega un nuevo TDR a la base de datos vectorial Y PostgreSQL.
    
    Esto permite que el sistema aprenda de los nuevos TDRs creados
    por los usuarios, mejorando las sugerencias futuras.
    También guarda el TDR en PostgreSQL para el historial del usuario.
    """
    try:
        # Generar ID único
        tdr_id = f"user_{request.tipo.value}_{uuid.uuid4().hex[:8]}"
        
        # Crear texto para embedding
        text_for_embedding = embedding_service.create_tdr_text(
            request.campos, 
            request.tipo.value
        )
        
        # Generar embedding
        embedding = embedding_service.get_embedding(text_for_embedding)
        
        # Preparar metadata
        metadata = {
            "filename": f"{request.titulo}.json",
            "category": f"Usuario_{request.tipo.value}",
            "tipo": request.tipo.value,
            "source": "frontend",
            "created_by": current_user.id,
            "created_at": datetime.now().isoformat(),
            "fields_json": json.dumps(request.campos, ensure_ascii=False)[:10000]
        }
        
        # Agregar a ChromaDB (para RAG)
        chroma_client.add_tdr(
            id=tdr_id,
            embedding=embedding,
            metadata=metadata,
            document=text_for_embedding
        )
        
        # Guardar en PostgreSQL (para historial del usuario)
        tdr_generado = TdrGenerado(
            id=tdr_id,
            user_id=current_user.id,
            tipo=request.tipo.value,
            titulo=request.titulo,
            datos_json=request.campos
        )
        db.add(tdr_generado)
        db.commit()
        db.refresh(tdr_generado)
        
        # Obtener estadísticas actualizadas
        stats = chroma_client.get_stats()
        
        return {
            "success": True,
            "message": "TDR agregado exitosamente a la base de conocimiento",
            "tdr_id": tdr_id,
            "total_tdrs": stats["total_tdrs"]
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error al agregar TDR: {str(e)}"
        )

