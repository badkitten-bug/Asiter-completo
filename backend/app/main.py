"""
Backend TDR Generator - API Principal.

Este servidor proporciona:
- Búsqueda de TDRs similares (BD vectorial)
- Generación de campos con RAG
- API REST para el frontend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .api.tdr import router as tdr_router
from .api.auth import router as auth_router
from .db.postgres import engine, Base
from .db.sql_models import User, TdrGenerado

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events: startup y shutdown."""
    # Startup: Crear tablas si no existen
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: cleanup si es necesario

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    description="""
    API para generación inteligente de TDRs usando RAG.
    
    ## Funcionalidades
    
    - 🔍 **Búsqueda semántica**: Encuentra TDRs similares en la base de datos
    - 🤖 **Generación RAG**: Genera campos automáticamente basándose en TDRs existentes
    - 📊 **Estadísticas**: Consulta estadísticas de la base de datos
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS para el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(tdr_router)
app.include_router(auth_router)


@app.get("/")
async def root():
    """Información del servicio."""
    return {
        "service": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check."""
    from .db.chroma import chroma_client
    
    stats = chroma_client.get_stats()
    
    return {
        "status": "healthy",
        "database": "chromadb",
        "total_tdrs": stats["total_tdrs"],
        "ready": stats["total_tdrs"] > 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )

