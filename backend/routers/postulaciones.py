from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import datetime
import os
import shutil

from database import get_db
from models import Usuario, Convocatoria, Postulacion, Documento, TipoDocumento
from schemas import PostulacionRequest, PostulacionResponse
from auth import obtener_usuario_actual

router = APIRouter(prefix="/api/postulaciones", tags=["Postulaciones"])

UPLOAD_DIR = "uploads"

def to_response(p: Postulacion) -> PostulacionResponse:
    programa = p.estudiante.programa.nombre if p.estudiante.programa else ""
    return PostulacionResponse(
        id=p.id,
        convocatoria=p.convocatoria.titulo,
        universidad=p.convocatoria.universidad.nombre,
        pais=p.convocatoria.universidad.pais,
        estado=p.estado,
        comentarioAdmin=p.comentario_admin,
        fechaPostulacion=p.fecha_postulacion,
        fechaActualizacion=p.fecha_actualizacion,
        estudiante=f"{p.estudiante.nombre} {p.estudiante.apellido}",
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

    carpeta = os.path.join(UPLOAD_DIR, str(id))
    os.makedirs(carpeta, exist_ok=True)

    archivos_subidos = []
    pares = [
        (certificado, "Certificado de notas", 1),
        (paz_y_salvo, "Paz y salvo académico", 2)
    ]

    for archivo, nombre_tipo, tipo_id in pares:
        if archivo and archivo.filename:
            if not archivo.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"El archivo '{archivo.filename}' debe ser PDF")

            ruta = os.path.join(carpeta, archivo.filename)
            with open(ruta, "wb") as f:
                shutil.copyfileobj(archivo.file, f)

            # Eliminar documento previo del mismo tipo si existe
            db.query(Documento).filter(
                Documento.postulacion_id == id,
                Documento.tipo_documento_id == tipo_id
            ).delete()

            doc = Documento(
                postulacion_id=id,
                nombre_archivo=archivo.filename,
                tipo_documento_id=tipo_id,
                ruta_archivo=ruta,
                fecha_subida=datetime.datetime.now()
            )
            db.add(doc)
            archivos_subidos.append(archivo.filename)

    db.commit()
    return {"mensaje": f"{len(archivos_subidos)} documento(s) subido(s) correctamente", "archivos": archivos_subidos}
