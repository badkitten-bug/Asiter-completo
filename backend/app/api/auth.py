"""
Endpoints de autenticación para verificar sesiones de Better Auth.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.postgres import get_db
from ..db.sql_models import User
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class SessionResponse(BaseModel):
    """Respuesta de verificación de sesión."""
    authenticated: bool
    user: dict | None = None


@router.get("/session", response_model=SessionResponse)
async def verify_session(
    current_user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verifica si hay una sesión activa de Better Auth.
    
    El frontend envía el token en el header Authorization.
    """
    if not current_user:
        return SessionResponse(authenticated=False, user=None)
    
    return SessionResponse(
        authenticated=True,
        user={
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "image": current_user.image
        }
    )

