"""
Conexión y operaciones con ChromaDB.
"""
import json
from pathlib import Path
from typing import Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from ..config import get_settings
from .models import TdrTipo, TdrSearchResult


class ChromaDBClient:
    """Cliente para ChromaDB."""
    
    _instance = None
    _client = None
    _collection = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            settings = get_settings()
            
            # Crear directorio si no existe
            persist_dir = Path(settings.chroma_persist_dir)
            persist_dir.mkdir(parents=True, exist_ok=True)
            
            # Inicializar cliente persistente
            self._client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Obtener o crear colección
            self._collection = self._client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"description": "TDRs del estado peruano"}
            )
    
    @property
    def collection(self):
        return self._collection
    
    def add_tdr(
        self,
        id: str,
        embedding: list[float],
        metadata: dict[str, Any],
        document: str
    ) -> None:
        """Añade un TDR a la colección."""
        self._collection.add(
            ids=[id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[document]
        )
    
    def add_tdrs_batch(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
        documents: list[str]
    ) -> None:
        """Añade múltiples TDRs en batch."""
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
    
    def search(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        tipo: Optional[TdrTipo] = None
    ) -> list[TdrSearchResult]:
        """Busca TDRs similares."""
        where_filter = None
        if tipo:
            where_filter = {"tipo": tipo.value}
        
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
            include=["metadatas", "documents", "distances"]
        )
        
        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 1.0
                
                # Convertir distancia a similaridad (ChromaDB usa L2 por defecto)
                similarity = 1 / (1 + distance)
                
                # Parsear fields del metadata
                fields = {}
                if "fields_json" in metadata:
                    try:
                        fields = json.loads(metadata["fields_json"])
                    except json.JSONDecodeError:
                        pass
                
                search_results.append(TdrSearchResult(
                    id=id,
                    filename=metadata.get("filename", ""),
                    tipo=TdrTipo(metadata.get("tipo", "SERVICIO")),
                    similarity=similarity,
                    fields=fields
                ))
        
        return search_results
    
    def get_stats(self) -> dict[str, Any]:
        """Obtiene estadísticas de la colección."""
        count = self._collection.count()
        
        # Obtener todos los metadatas para estadísticas
        if count > 0:
            all_data = self._collection.get(include=["metadatas"])
            
            por_tipo = {}
            por_categoria = {}
            
            for metadata in all_data["metadatas"]:
                tipo = metadata.get("tipo", "UNKNOWN")
                categoria = metadata.get("category", "UNKNOWN")
                
                por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
                por_categoria[categoria] = por_categoria.get(categoria, 0) + 1
        else:
            por_tipo = {}
            por_categoria = {}
        
        return {
            "total_tdrs": count,
            "por_tipo": por_tipo,
            "por_categoria": por_categoria
        }
    
    def clear(self) -> None:
        """Limpia la colección."""
        self._client.delete_collection(get_settings().chroma_collection_name)
        self._collection = self._client.create_collection(
            name=get_settings().chroma_collection_name,
            metadata={"description": "TDRs del estado peruano"}
        )


# Instancia global
chroma_client = ChromaDBClient()

