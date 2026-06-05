from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Usuario, Postulacion, Documento, Convocatoria
from schemas import PostulacionResponse, DocumentoResponse
from auth import solo_universidad
from routers.postulaciones import to_response

router = APIRouter(prefix="/api/universidad", tags=["Universidad Destino"])

@router.get("/mis-estudiantes", response_model=List[PostulacionResponse],
            summary="Ver estudiantes que vienen a mi universidad")
def mis_estudiantes(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(solo_universidad)
):
    """
    Devuelve las postulaciones de estudiantes que van a la universidad
    del usuario autenticado.
    """
    if not usuario.universidad_id:
        raise HTTPException(status_code=400, detail="El usuario no tiene una universidad asociada")

    postulaciones = (
        db.query(Postulacion)
        .join(Convocatoria)
        .filter(Convocatoria.universidad_id == usuario.universidad_id)
        .order_by(Postulacion.fecha_postulacion.desc())
        .all()
    )
    return [to_response(p) for p in postulaciones]

@router.get("/postulaciones/{id}/documentos", response_model=List[DocumentoResponse],
            summary="Ver documentos de un estudiante entrante")
def ver_documentos(
    id: int, 
    db: Session = Depends(get_db), 
    usuario: Usuario = Depends(solo_universidad)
):
    postulacion = db.query(Postulacion).filter(Postulacion.id == id).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    
    # Verificar que la postulación pertenezca a la universidad del usuario
    if postulacion.convocatoria.universidad_id != usuario.universidad_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver estos documentos")

    docs = db.query(Documento).filter(Documento.postulacion_id == id).all()
    return [
        DocumentoResponse(
            id=d.id,
            nombre_archivo=d.nombre_archivo,
            tipo=d.tipo_documento.nombre if d.tipo_documento else None,
            s3_key=d.s3_key,
            fecha_subida=d.fecha_subida
        ) for d in docs
    ]
