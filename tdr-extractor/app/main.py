"""
TDR Extractor - Microservicio FastAPI para extracción de campos desde PDFs.

Endpoints:
- POST /extract-tdr: Recibe un PDF y devuelve JSON con campos extraídos
- GET /health: Health check del servicio
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .ocr import extract_text_from_bytes
from .extractor import extract_tdr_fields

# Configuración
settings = get_settings()

# Crear directorio de uploads si no existe
uploads_dir = Path(settings.upload_dir)
uploads_dir.mkdir(exist_ok=True)

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    description="Microservicio para extracción de campos desde PDFs de TDR usando OCR y LLM",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS para permitir conexiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Next.js dev
        "http://127.0.0.1:3000",
        "http://localhost:5173",      # Vite dev
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Endpoint raíz con información del servicio."""
    return {
        "service": settings.app_name,
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check del servicio."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "config": {
            "use_local_llm": settings.use_local_llm,
            "ollama_model": settings.ollama_model if settings.use_local_llm else None,
            "deepseek_model": settings.deepseek_model if not settings.use_local_llm else None,
        }
    }


@app.post("/extract-tdr")
async def extract_tdr(
    file: UploadFile = File(..., description="Archivo PDF del TDR"),
    save_pdf: bool = Query(False, description="Guardar el PDF en el servidor"),
):
    """
    Extrae campos de un PDF de TDR.
    
    1. Recibe el archivo PDF
    2. Extrae el texto (OCR si es necesario)
    3. Envía al LLM para extraer campos
    4. Devuelve JSON flexible con los campos detectados
    
    Args:
        file: Archivo PDF a procesar
        save_pdf: Si True, guarda una copia del PDF
        
    Returns:
        JSON con:
        - success: bool indicando si la extracción fue exitosa
        - filename: Nombre del archivo original
        - extraction_method: 'digital' u 'ocr'
        - page_count: Número de páginas
        - fields: Campos extraídos del TDR (esquema flexible)
        - raw_text: Texto crudo extraído (opcional)
    """
    # Validar tipo de archivo
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser un PDF"
        )
    
    # Leer contenido del archivo
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al leer el archivo: {str(e)}"
        )
    
    # Validar tamaño
    max_size = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo excede el límite de {settings.max_file_size_mb}MB"
        )
    
    # Guardar PDF si se solicita
    saved_path = None
    if save_pdf:
        file_id = str(uuid.uuid4())
        saved_path = uploads_dir / f"{file_id}.pdf"
        with open(saved_path, "wb") as f:
            f.write(content)
    
    # Extraer texto del PDF
    try:
        ocr_result = extract_text_from_bytes(content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en la extracción de texto: {str(e)}"
        )
    
    # Verificar que hay texto para procesar
    if not ocr_result.get("text", "").strip():
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "filename": file.filename,
                "extraction_method": ocr_result.get("method"),
                "page_count": ocr_result.get("page_count", 0),
                "error": "No se pudo extraer texto del PDF",
                "fields": {},
            }
        )
    
    # Extraer campos con LLM
    try:
        extracted_fields = await extract_tdr_fields(ocr_result["text"])
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en la extracción de campos con LLM: {str(e)}"
        )
    
    # Preparar respuesta
    response = {
        "success": True,
        "filename": file.filename,
        "extraction_method": ocr_result.get("method", "unknown"),
        "page_count": ocr_result.get("page_count", 0),
        "fields": extracted_fields,
        "metadata": {
            "processed_at": datetime.utcnow().isoformat(),
            "saved_path": str(saved_path) if saved_path else None,
            "text_length": len(ocr_result.get("text", "")),
        }
    }
    
    # Incluir advertencias si existen
    if "warning" in ocr_result:
        response["warning"] = ocr_result["warning"]
    
    return response


@app.post("/extract-text")
async def extract_text_only(
    file: UploadFile = File(..., description="Archivo PDF"),
):
    """
    Extrae solo el texto de un PDF sin procesarlo con LLM.
    
    Útil para debugging o cuando solo necesitas el texto crudo.
    """
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser un PDF"
        )
    
    try:
        content = await file.read()
        result = extract_text_from_bytes(content)
        
        return {
            "success": True,
            "filename": file.filename,
            "method": result.get("method"),
            "page_count": result.get("page_count", 0),
            "text": result.get("text", ""),
            "pages": result.get("pages", []),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al extraer texto: {str(e)}"
        )


# Manejo de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de excepciones."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "detail": "Error interno del servidor",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

