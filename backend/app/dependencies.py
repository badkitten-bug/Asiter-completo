"""
Dependencies para FastAPI (autenticación, base de datos, etc.)
"""
from typing import Optional
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
import jwt

from .db.postgres import get_db
from .db.sql_models import User
from .config import get_settings

settings = get_settings()


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency para obtener el usuario actual.
    
    Soporta dos métodos:
    1. Token JWT en header Authorization (Bearer token)
    2. User ID directo en header X-User-Id (para Better Auth con cookies)
    """
    user_id = None
    
    # Método 1: Intentar obtener user_id del header X-User-Id (más simple para Better Auth)
    if x_user_id:
        user_id = x_user_id
    # Método 2: Intentar decodificar token JWT
    elif authorization:
        try:
            # Better Auth envía tokens como "Bearer <token>"
            token = authorization.replace("Bearer ", "")
            
            # Decodificar token (Better Auth usa el secret)
            payload = jwt.decode(
                token,
                settings.better_auth_secret,
                algorithms=["HS256"],
                options={"verify_signature": True}
            )
            
            user_id = payload.get("userId") or payload.get("user_id") or payload.get("sub")
        except (jwt.InvalidTokenError, Exception):
            # Si falla el token, intentar con X-User-Id si está disponible
            pass
    
    if not user_id:
        return None
    
    # Buscar usuario en la BD
    user = db.query(User).filter(User.id == user_id).first()
    
    # Si no existe, crearlo (esto puede pasar si el usuario se registró en Better Auth
    # pero aún no se ha sincronizado con nuestra BD)
    if not user:
        # Intentar obtener más info del token si está disponible
        email = ""
        name = "Usuario"
        image = None
        
        if authorization:
            try:
                token = authorization.replace("Bearer ", "")
                payload = jwt.decode(
                    token,
                    settings.better_auth_secret,
                    algorithms=["HS256"],
                    options={"verify_signature": False}  # Solo para leer datos
                )
                email = payload.get("email") or ""
                name = payload.get("name") or email.split("@")[0] if email else "Usuario"
                image = payload.get("image")
            except:
                pass
        
        user = User(
            id=user_id,
            email=email or f"user_{user_id[:8]}@asiter.com",
            name=name,
            image=image
        )
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()
            return None
    
    return user


async def require_auth(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    Dependency que requiere autenticación.
    Lanza HTTPException si el usuario no está autenticado.
    """
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="No autenticado. Por favor inicia sesión."
        )
    return current_user

