"""
Configuración del microservicio TDR Extractor.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Configuración de la aplicación."""
    
    # Servidor
    app_name: str = "TDR Extractor API"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Directorios
    upload_dir: str = "uploads"
    
    # OCR Settings
    tesseract_cmd: str | None = None  # Ruta a tesseract, None para usar PATH
    ocr_language: str = "spa"  # Español por defecto
    
    # LLM Settings - DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    
    # LLM Settings - Local (Ollama)
    use_local_llm: bool = True
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "deepseek-r1:8b"  # o qwen2.5:14b, mistral, etc.
    
    # Límites
    max_file_size_mb: int = 50
    max_pages: int = 100
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Obtiene la configuración cacheada."""
    return Settings()

