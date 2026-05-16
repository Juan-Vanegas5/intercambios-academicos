from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Usuario, Postulacion, Documento
from schemas import EstadoRequest, PostulacionResponse, DocumentoResponse
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

@router.get("/postulaciones/{id}/documentos", response_model=List[DocumentoResponse],
            summary="Ver documentos de una postulación")
def ver_documentos(
    id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(solo_admin)
):
    """Devuelve los documentos subidos para una postulación."""
    if not db.query(Postulacion).filter(Postulacion.id == id).first():
        raise HTTPException(status_code=404, detail="Postulación no encontrada")

    docs = db.query(Documento).filter(Documento.postulacion_id == id).all()
    return [
        DocumentoResponse(
            id=d.id,
            nombre_archivo=d.nombre_archivo,
            tipo=d.tipo_documento.nombre if d.tipo_documento else None,
            ruta_archivo=d.ruta_archivo,
            fecha_subida=d.fecha_subida
        ) for d in docs
    ]

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
