from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Convocatoria

router = APIRouter(prefix="/api/convocatorias", tags=["Convocatorias"])

@router.get("", summary="Listar convocatorias activas")
def listar_activas(db: Session = Depends(get_db)):
    """Devuelve las convocatorias con estado 'activa'. No requiere token."""
    return db.query(Convocatoria).filter(Convocatoria.estado == "activa").all()

@router.get("/todas", summary="Listar todas las convocatorias")
def listar_todas(db: Session = Depends(get_db)):
    """Devuelve todas las convocatorias sin importar el estado. Requiere token."""
    return db.query(Convocatoria).order_by(Convocatoria.fecha_cierre).all()

@router.get("/{id}", summary="Ver detalle de una convocatoria")
def detalle(id: int, db: Session = Depends(get_db)):
    convocatoria = db.query(Convocatoria).filter(Convocatoria.id == id).first()
    if not convocatoria:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")
    return convocatoria
