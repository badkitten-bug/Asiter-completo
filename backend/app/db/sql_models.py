"""
Modelos SQLAlchemy para PostgreSQL.
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .postgres import Base


class User(Base):
    """Modelo de usuario."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    image = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relación con TDRs
    tdrs = relationship("TdrGenerado", back_populates="user", cascade="all, delete-orphan")


class TdrGenerado(Base):
    """Modelo de TDR generado por usuario."""
    __tablename__ = "tdrs_generados"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(String, nullable=False, index=True)  # BIEN, SERVICIO, OBRA, CONSULTORIA_OBRA
    titulo = Column(String, nullable=False)
    datos_json = Column(JSON, nullable=False)  # Todos los campos del TDR en formato JSON
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relación con usuario
    user = relationship("User", back_populates="tdrs")

