from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class ProgramaAcademico(Base):
    __tablename__ = "programas_academicos"
    id      = Column(Integer, primary_key=True)
    nombre  = Column(String(100), nullable=False, unique=True)

class Universidad(Base):
    __tablename__ = "universidades"
    id      = Column(Integer, primary_key=True)
    nombre  = Column(String(200), nullable=False)
    pais    = Column(String(100), nullable=False)

class TipoDocumento(Base):
    __tablename__ = "tipos_documentos"
    id      = Column(Integer, primary_key=True)
    nombre  = Column(String(50), nullable=False, unique=True)

class Usuario(Base):
    __tablename__ = "usuarios"
    id              = Column(Integer, primary_key=True)
    nombre          = Column(String(100), nullable=False)
    apellido        = Column(String(100), nullable=False)
    email           = Column(String(150), nullable=False, unique=True)
    contrasena      = Column(String(255), nullable=False)
    rol             = Column(String(20), nullable=False)
    codigo          = Column(String(20))
    programa_id     = Column(Integer, ForeignKey("programas_academicos.id"))
    fecha_registro  = Column(DateTime, default=datetime.datetime.now)

    programa = relationship("ProgramaAcademico", lazy="joined")

class Convocatoria(Base):
    __tablename__ = "convocatorias"
    id              = Column(Integer, primary_key=True)
    titulo          = Column(String(200), nullable=False)
    universidad_id  = Column(Integer, ForeignKey("universidades.id"))
    descripcion     = Column(Text)
    requisitos      = Column(Text)
    fecha_inicio    = Column(Date, nullable=False)
    fecha_cierre    = Column(Date, nullable=False)
    cupos           = Column(Integer, nullable=False, default=1)
    estado          = Column(String(20), nullable=False)
    creado_por      = Column(Integer, ForeignKey("usuarios.id"))
    fecha_creacion  = Column(DateTime, default=datetime.datetime.now)

    universidad = relationship("Universidad", lazy="joined")

class Postulacion(Base):
    __tablename__ = "postulaciones"
    id                  = Column(Integer, primary_key=True)
    estudiante_id       = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    convocatoria_id     = Column(Integer, ForeignKey("convocatorias.id"), nullable=False)
    estado              = Column(String(20), nullable=False, default="en_revision")
    comentario_admin    = Column(Text)
    fecha_postulacion   = Column(DateTime, default=datetime.datetime.now)
    fecha_actualizacion = Column(DateTime, default=datetime.datetime.now)

    estudiante   = relationship("Usuario", lazy="joined")
    convocatoria = relationship("Convocatoria", lazy="joined")
