from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import datetime

from database import get_db
from models import Usuario, Convocatoria, Postulacion
from schemas import PostulacionRequest, PostulacionResponse
from auth import obtener_usuario_actual

router = APIRouter(prefix="/api/postulaciones", tags=["Postulaciones"])

def to_response(p: Postulacion) -> PostulacionResponse:
    return PostulacionResponse(
        id=p.id,
        convocatoria=p.convocatoria.titulo,
        universidad=p.convocatoria.universidad.nombre,
        pais=p.convocatoria.universidad.pais,
        estado=p.estado,
        comentarioAdmin=p.comentario_admin,
        fechaPostulacion=p.fecha_postulacion,
        fechaActualizacion=p.fecha_actualizacion
    )

@router.get("/mis", response_model=List[PostulacionResponse],
            summary="Ver mis postulaciones")
def mis_postulaciones(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual)
):
    """Devuelve las postulaciones del estudiante autenticado con su estado actual."""
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
    """El estudiante se postula a una convocatoria activa. Solo puede postularse una vez."""
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
