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
    verificacionUniversidad: Optional[str] = None
    comentarioUniversidad: Optional[str] = None
    fechaVerificacionUniversidad: Optional[datetime] = None
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
    s3_key: str
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

class TOTPSetupResponse(BaseModel):
    qr_code: str
    secret: str
    email: str

class TOTPVerifyRequest(BaseModel):
    email: str
    codigo: str

class TOTPConfirmSetupRequest(BaseModel):
    email: str
    secret: str
    codigo: str

class EstadoRequest(BaseModel):
    estado: str
    comentario: Optional[str] = None

class SeleccionGanadoresRequest(BaseModel):
    ids_seleccionados: List[int]
    comentario: Optional[str] = None

class ConvocatoriaCreate(BaseModel):
    titulo: str
    universidad_id: int
    descripcion: Optional[str] = None
    requisitos: Optional[str] = None
    fecha_inicio: str
    fecha_cierre: str
    cupos: int
    estado: str

class ConvocatoriaUpdate(BaseModel):
    titulo: Optional[str] = None
    universidad_id: Optional[int] = None
    descripcion: Optional[str] = None
    requisitos: Optional[str] = None
    fecha_inicio: Optional[str] = None
    fecha_cierre: Optional[str] = None
    cupos: Optional[int] = None
    estado: Optional[str] = None

class UniversidadCreate(BaseModel):
    nombre: str
    pais: str

class UniversidadUpdate(BaseModel):
    nombre: Optional[str] = None
    pais: Optional[str] = None
