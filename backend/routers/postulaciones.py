from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import datetime
import os
import boto3
from botocore.exceptions import NoCredentialsError

from database import get_db
from models import Usuario, Convocatoria, Postulacion, Documento, TipoDocumento
from schemas import PostulacionRequest, PostulacionResponse
from auth import obtener_usuario_actual
from s3_service import subir_a_s3

router = APIRouter(prefix="/api/postulaciones", tags=["Postulaciones"])

def to_response(p: Postulacion) -> PostulacionResponse:
    programa = p.estudiante.programa.nombre if p.estudiante.programa else ""
    return PostulacionResponse(
        id=p.id,
        convocatoria=p.convocatoria.titulo,
        universidad=p.convocatoria.universidad.nombre,
        pais=p.convocatoria.universidad.pais,
        estado=p.estado,
        semestre=p.semestre,
        cartaIntencion=p.carta_intencion,
        comentarioAdmin=p.comentario_admin,
        fechaPostulacion=p.fecha_postulacion,
        fechaActualizacion=p.fecha_actualizacion,
        estudiante=f"{p.estudiante.nombre} {p.estudiante.apellido}",
        cedula=p.estudiante.cedula,
        celular=p.estudiante.celular,
        programa=programa,
        documentos=len(p.documentos) if p.documentos else 0
    )

@router.get("/mis", response_model=List[PostulacionResponse],
            summary="Ver mis postulaciones")
def mis_postulaciones(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual)
):
    """Devuelve las postulaciones del estudiante autenticado."""
    postulaciones = (
        db.query(Postulacion)
        .filter(Postulacion.estudiante_id == usuario.id)
        .order_by(Postulacion.fecha_postulacion.desc())
        .all()
    )
    return [to_response(p) for p in postulaciones]

@router.post("", response_model=PostulacionResponse, summary="Crear postulación")
def postular(
    request: PostulacionRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual)
):
    """El estudiante se postula a una convocatoria activa."""
    convocatoria = db.query(Convocatoria).filter(Convocatoria.id == request.convocatoriaId).first()
    if not convocatoria:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")
    if convocatoria.estado != "activa":
        raise HTTPException(status_code=400, detail="La convocatoria no está activa")

    existe = db.query(Postulacion).filter(
        Postulacion.estudiante_id == usuario.id,
        Postulacion.convocatoria_id == convocatoria.id
    ).first()
    if existe:
        raise HTTPException(status_code=400, detail="Ya tienes una postulación en esta convocatoria")

    nueva = Postulacion(
        estudiante_id=usuario.id,
        convocatoria_id=convocatoria.id,
        semestre=request.semestre,
        carta_intencion=request.cartaIntencion,
        estado="en_revision",
        fecha_postulacion=datetime.datetime.now(),
        fecha_actualizacion=datetime.datetime.now()
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return to_response(nueva)

@router.post("/{id}/documentos", summary="Subir documentos PDF")
async def subir_documentos(
    id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
    certificado: UploadFile = File(None),
    paz_y_salvo: UploadFile = File(None)
):
    """Sube los documentos PDF adjuntos a una postulación del estudiante."""
    postulacion = db.query(Postulacion).filter(
        Postulacion.id == id,
        Postulacion.estudiante_id == usuario.id
    ).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")

    archivos_subidos = []
    pares = [
        (certificado, "Certificado de notas", 1),
        (paz_y_salvo, "Paz y salvo académico", 2)
    ]

    for archivo, nombre_tipo, tipo_id in pares:
        if archivo and archivo.filename:
            if not archivo.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"El archivo '{archivo.filename}' debe ser PDF")

            # SUBIR A S3
            url_s3 = subir_a_s3(archivo, str(id))

            # Eliminar registro previo del mismo tipo en la BD si existe
            db.query(Documento).filter(
                Documento.postulacion_id == id,
                Documento.tipo_documento_id == tipo_id
            ).delete()

            # Guardar nueva URL en la BD
            doc = Documento(
                postulacion_id=id,
                nombre_archivo=archivo.filename,
                tipo_documento_id=tipo_id,
                s3_key=url_s3,
                fecha_subida=datetime.datetime.now()
            )
            db.add(doc)
            archivos_subidos.append(archivo.filename)

    db.commit()
    return {"mensaje": f"{len(archivos_subidos)} documento(s) subido(s) a S3 correctamente", "archivos": archivos_subidos}

DOCS_VIAJE = [
    ("vuelos",  "Tiquetes de vuelo",     3),
    ("seguro",  "Seguro médico",         4),
    ("visa",    "Visa",                  5),
    ("pasaporte","Pasaporte",            6),
]

@router.post("/{id}/documentos-viaje", summary="Subir documentos de segunda fase (viaje)")
async def subir_documentos_viaje(
    id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
    vuelos:    UploadFile = File(None),
    seguro:    UploadFile = File(None),
    visa:      UploadFile = File(None),
    pasaporte: UploadFile = File(None)
):
    """Sube los documentos de viaje (segunda fase) para una postulación aprobada."""
    postulacion = db.query(Postulacion).filter(
        Postulacion.id == id,
        Postulacion.estudiante_id == usuario.id
    ).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    if postulacion.estado not in ["aprobada", "necesita_correcciones_viaje"]:
        raise HTTPException(status_code=400, detail="Solo puedes subir documentos de viaje cuando tu postulación está aprobada o requiere correcciones de viaje")

    archivos = [vuelos, seguro, visa, pasaporte]
    subidos = []

    for archivo, (campo, nombre_tipo, tipo_id) in zip(archivos, DOCS_VIAJE):
        if archivo and archivo.filename:
            if not archivo.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"'{archivo.filename}' debe ser PDF")

            # Asegurar que el TipoDocumento existe
            tipo = db.query(TipoDocumento).filter(TipoDocumento.id == tipo_id).first()
            if not tipo:
                tipo = TipoDocumento(id=tipo_id, nombre=nombre_tipo)
                db.add(tipo)
                db.flush()

            # SUBIR A S3
            url_s3 = subir_a_s3(archivo, str(id))

            # Eliminar registro previo en la BD
            db.query(Documento).filter(
                Documento.postulacion_id == id,
                Documento.tipo_documento_id == tipo_id
            ).delete()

            # Guardar nueva URL en la BD
            db.add(Documento(
                postulacion_id=id,
                nombre_archivo=archivo.filename,
                tipo_documento_id=tipo_id,
                s3_key=url_s3,
                fecha_subida=datetime.datetime.now()
            ))
            subidos.append(archivo.filename)

    if subidos:
        postulacion.estado = "docs_viaje_enviados"
    db.commit()
    return {"mensaje": f"{len(subidos)} documento(s) de viaje subido(s) a S3", "archivos": subidos}
