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
    estudiante: Optional[str] = None
    programa: Optional[str] = None
    documentos: Optional[int] = 0

class RegistroRequest(BaseModel):
    nombre: str
    apellido: str
    email: str
    contrasena: str
    codigo: str
    programa: str

class EstadoRequest(BaseModel):
    estado: str
    comentario: Optional[str] = None
