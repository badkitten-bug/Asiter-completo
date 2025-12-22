"""
Conexión y operaciones con PostgreSQL usando SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from ..config import get_settings

settings = get_settings()

# Crear engine
# Si no hay DATABASE_URL configurado o es el valor por defecto, usar SQLite como fallback para desarrollo
database_url = getattr(settings, 'database_url', None) or "sqlite:///./asiter.db"

# Detectar si es una URL de PostgreSQL con valores por defecto o inválidos
# Si contiene "user:password" o valores por defecto, usar SQLite
if database_url and database_url.startswith("postgresql://"):
    # Verificar si tiene credenciales por defecto o inválidas
    default_patterns = [
        "user:password",
        "postgresql://user:password",
        "postgresql://postgres:password",
        "@localhost:5432/asiter"
    ]
    
    if any(pattern in database_url for pattern in default_patterns):
        database_url = "sqlite:///./asiter.db"
        print("⚠️  Usando SQLite para desarrollo. Configura PostgreSQL en .env para producción.")

engine = create_engine(
    database_url,
    pool_pre_ping=True if "sqlite" not in database_url else False,
    pool_size=5 if "sqlite" not in database_url else 1,
    max_overflow=10 if "sqlite" not in database_url else 0,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
)

# SessionLocal para dependency injection
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obtener sesión de base de datos.
    Usar en FastAPI: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

