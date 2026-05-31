from pydantic import BaseModel
from typing import Optional, List
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
    semestre: Optional[int] = None
    cartaIntencion: Optional[str] = None

class PostulacionResponse(BaseModel):
    id: int
    convocatoria: str
    universidad: str
    pais: str
    estado: str
    semestre: Optional[int] = None
    cartaIntencion: Optional[str] = None
    comentarioAdmin: Optional[str] = None
    fechaPostulacion: Optional[datetime] = None
    fechaActualizacion: Optional[datetime] = None
    estudiante: Optional[str] = None
    cedula: Optional[str] = None
    celular: Optional[str] = None
    programa: Optional[str] = None
    documentos: Optional[int] = 0

class DocumentoResponse(BaseModel):
    id: int
    nombre_archivo: str
    tipo: Optional[str] = None
    ruta_archivo: str
    fecha_subida: Optional[datetime] = None

class RegistroRequest(BaseModel):
    nombre: str
    apellido: str
    email: str
    contrasena: str
    codigo: str
    cedula: str
    celular: str
    programa: str

class VerificarCodigoRequest(BaseModel):
    email: str
    codigo: str

class EstadoRequest(BaseModel):
    estado: str
    comentario: Optional[str] = None

class SeleccionGanadoresRequest(BaseModel):
    ids_seleccionados: List[int]
    comentario: Optional[str] = None
