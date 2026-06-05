from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
import re

EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$')

class LoginRequest(BaseModel):
    email: str
    contrasena: str

    @field_validator('email')
    @classmethod
    def validar_email(cls, v):
        if not EMAIL_REGEX.match(v.strip()):
            raise ValueError('El correo no es válido. Debe tener el formato: ejemplo@dominio.com')
        return v.strip().lower()

class LoginResponse(BaseModel):
    token: str
    nombre: str
    apellido: str
    email: str
    rol: str
    universidad_id: Optional[int] = None

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
    estudianteEmail: Optional[str] = None
    cedula: Optional[str] = None
    celular: Optional[str] = None
    programa: Optional[str] = None
    documentos: Optional[int] = 0

class DocumentoResponse(BaseModel):
    id: int
    nombre_archivo: str
    tipo: Optional[str] = None
<<<<<<< HEAD
    mimetype: Optional[str] = "application/pdf"
=======
    s3_key: str
>>>>>>> main
    fecha_subida: Optional[datetime] = None

    class Config:
        from_attributes = True

class RegistroRequest(BaseModel):
    nombre: str
    apellido: str
    email: str
    contrasena: str
    codigo: str
    cedula: str
    celular: str
    programa: str

    @field_validator('email')
    @classmethod
    def validar_email(cls, v):
        if not EMAIL_REGEX.match(v.strip()):
            raise ValueError('El correo no es válido. Debe tener el formato: ejemplo@dominio.com')
        return v.strip().lower()

    @field_validator('nombre', 'apellido')
    @classmethod
    def validar_solo_letras(cls, v):
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ\s]+$', v.strip()):
            raise ValueError('El nombre y apellido solo pueden contener letras, no números ni símbolos.')
        return v.strip()

class VerificarCodigoRequest(BaseModel):
    email: str
    codigo: str

<<<<<<< HEAD
class ConfirmarRegistroRequest(BaseModel):
    email: str
    codigo: str

class ReenviarVerificacionRequest(BaseModel):
    email: str
=======
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
>>>>>>> main

class EstadoRequest(BaseModel):
    estado: str
    comentario: Optional[str] = None

<<<<<<< HEAD
class ConvocatoriaCreate(BaseModel):
    titulo: str
    universidadId: int
    descripcion: Optional[str] = None
    requisitos: Optional[str] = None
    fechaInicio: str
    fechaCierre: str
    cupos: int = 1
    estado: str = "activa"

class NotificacionResponse(BaseModel):
    id: int
    mensaje: str
    leida: bool
    fecha: Optional[datetime] = None
    tipo: Optional[str] = "postulacion"

class SeleccionGanadoresRequest(BaseModel):
    ids_seleccionados: List[int]
    comentario: Optional[str] = None
=======
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
>>>>>>> main
