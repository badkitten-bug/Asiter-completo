"""
Servicio de embeddings para TDRs.
"""
from typing import Any
from sentence_transformers import SentenceTransformer

from ..config import get_settings


class EmbeddingService:
    """Servicio para generar embeddings de texto."""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            settings = get_settings()
            print(f"[*] Cargando modelo de embeddings: {settings.embedding_model}")
            self._model = SentenceTransformer(settings.embedding_model)
            print("[OK] Modelo de embeddings cargado")
    
    def get_embedding(self, text: str) -> list[float]:
        """Genera embedding para un texto."""
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Genera embeddings para múltiples textos."""
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def create_tdr_text(self, fields: dict[str, Any], tipo: str) -> str:
        """
        Crea texto representativo del TDR para embedding.
        
        Combina los campos más importantes para crear un texto
        que capture la esencia del TDR.
        """
        parts = [f"Tipo: {tipo}"]
        
        # Campos prioritarios para el embedding
        priority_fields = [
            "objeto_contratacion",
            "denominacion_servicio", 
            "denominacionContratacion",
            "finalidad_publica",
            "finalidadPublica",
            "alcance",
            "alcanceDescripcionServicio",
            "servicios_requeridos",
            "requisitos_tecnicos_minimos",
            "perfil_profesional",
            "entregables"
        ]
        
        for field in priority_fields:
            if field in fields and fields[field]:
                value = fields[field]
                if isinstance(value, list):
                    if value and isinstance(value[0], dict):
                        # Lista de objetos, extraer textos
                        value = " | ".join([
                            str(v) for item in value[:3] 
                            for v in item.values() if v
                        ])
                    else:
                        value = " | ".join([str(v) for v in value[:5]])
                elif isinstance(value, dict):
                    value = " | ".join([f"{k}: {v}" for k, v in list(value.items())[:5]])
                
                parts.append(f"{field}: {value}")
        
        return "\n".join(parts)


# Instancia global
embedding_service = EmbeddingService()

