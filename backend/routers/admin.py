from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Usuario, Postulacion
from schemas import EstadoRequest, PostulacionResponse
from auth import solo_admin
from routers.postulaciones import to_response

router = APIRouter(prefix="/api/admin", tags=["Administración"])

@router.get("/postulaciones", response_model=List[PostulacionResponse],
            summary="Ver todas las postulaciones")
def todas(
    db: Session = Depends(get_db),
    admin: Usuario = Depends(solo_admin)
):
    """Solo administradores. Lista todas las postulaciones con datos del estudiante."""
    return [to_response(p) for p in db.query(Postulacion).all()]

@router.put("/postulaciones/{id}/estado", response_model=PostulacionResponse,
            summary="Aprobar o rechazar postulación")
def actualizar_estado(
    id: int,
    request: EstadoRequest,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(solo_admin)
):
    """Cambia el estado a 'aprobada' o 'rechazada' y agrega un comentario al estudiante."""
    if request.estado not in ["aprobada", "rechazada", "en_revision"]:
        raise HTTPException(status_code=400, detail="Estado inválido")

    postulacion = db.query(Postulacion).filter(Postulacion.id == id).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")

    postulacion.estado = request.estado
    postulacion.comentario_admin = request.comentario
    db.commit()
    db.refresh(postulacion)
    return to_response(postulacion)
