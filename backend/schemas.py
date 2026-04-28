from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    email: str
    contrasena: str

class LoginResponse(BaseModel):
    token: str
    nombre: str
    apellido: str
    email: str
    rol: str

class PostulacionRequest(BaseModel):
    convocatoriaId: int

class PostulacionResponse(BaseModel):
    id: int
    convocatoria: str
    universidad: str
    pais: str
    estado: str
    comentarioAdmin: Optional[str]
    fechaPostulacion: Optional[datetime]
    fechaActualizacion: Optional[datetime]

class EstadoRequest(BaseModel):
    estado: str           # "aprobada" | "rechazada"
    comentario: Optional[str] = None
