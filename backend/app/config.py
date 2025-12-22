"""
Configuración del backend TDR Generator.
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


def parse_cors_origins(origins_str: str) -> list[str]:
    """Parse CORS origins from comma-separated string."""
    if not origins_str:
        return ["http://localhost:3000", "http://localhost:3001"]
    return [origin.strip() for origin in origins_str.split(",") if origin.strip()]


class Settings(BaseSettings):
    """Configuración de la aplicación."""
    
    # Servidor
    app_name: str = "TDR Generator API"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8001  # Puerto diferente al extractor
    
    # CORS - Como string, se parseará después
    cors_origins_str: str = "http://localhost:3000,http://localhost:3002"
    
    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "tdrs"
    
    # Gemini API - DEBE configurarse via variable de entorno
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    
    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"  # Modelo local rápido
    
    # Rutas
    tdr_jsons_dir: str = "../tdr-extractor/output_gemini"
    
    # PostgreSQL/SQLite
    database_url: str = "sqlite:///./asiter.db"
    
    # Better Auth
    better_auth_secret: str = "asiter-default-secret-key-32chars!"
    
    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if not self.cors_origins_str:
            return ["http://localhost:3000", "http://localhost:3002"]
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

