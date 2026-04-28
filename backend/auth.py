from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import Usuario
from dotenv import load_dotenv
import os

load_dotenv()

JWT_SECRET          = os.getenv("JWT_SECRET", "cambiar_en_produccion")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
ALGORITHM           = "HS256"

pwd_context    = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme  = HTTPBearer()

def verificar_contrasena(raw: str, guardada: str) -> bool:
    # Soporta BCrypt (producción) y texto plano (datos de prueba)
    if guardada.startswith("$2"):
        return pwd_context.verify(raw, guardada)
    return raw == guardada

def generar_token(email: str, rol: str) -> str:
    payload = {
        "sub": email,
        "rol": rol,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

def obtener_usuario_actual(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[ALGORITHM])
        email   = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o vencido")

    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return usuario

def solo_admin(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
    if usuario.rol != "administrador":
        raise HTTPException(status_code=403, detail="Acceso solo para administradores")
    return usuario
