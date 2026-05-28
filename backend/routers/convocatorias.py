from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Convocatoria, Postulacion

router = APIRouter(prefix="/api/convocatorias", tags=["Convocatorias"])

def conv_to_dict(c: Convocatoria, db: Session = None) -> dict:
    total_postulaciones = 0
    if db:
        total_postulaciones = db.query(Postulacion).filter(
            Postulacion.convocatoria_id == c.id
        ).count()
    return {
        "id": c.id,
        "titulo": c.titulo,
        "universidad": c.universidad.nombre if c.universidad else "",
        "pais": c.universidad.pais if c.universidad else "",
        "ciudad": c.universidad.ciudad if c.universidad else None,
        "latitud": c.universidad.latitud if c.universidad else None,
        "longitud": c.universidad.longitud if c.universidad else None,
        "descripcion": c.descripcion,
        "requisitos": c.requisitos,
        "fechaInicio": str(c.fecha_inicio),
        "fechaCierre": str(c.fecha_cierre),
        "cupos": c.cupos,
        "estado": c.estado,
        "totalPostulaciones": total_postulaciones,
    }

@router.get("", summary="Listar convocatorias activas")
def listar_activas(db: Session = Depends(get_db)):
    """Devuelve convocatorias con estado 'activa'. No requiere token."""
    return [conv_to_dict(c, db) for c in
            db.query(Convocatoria).filter(Convocatoria.estado == "activa").all()]

@router.get("/todas", summary="Listar todas las convocatorias")
def listar_todas(db: Session = Depends(get_db)):
    """Devuelve todas las convocatorias sin importar el estado."""
    return [conv_to_dict(c, db) for c in
            db.query(Convocatoria).order_by(Convocatoria.fecha_cierre).all()]

@router.get("/{id}", summary="Ver detalle de una convocatoria")
def detalle(id: int, db: Session = Depends(get_db)):
    c = db.query(Convocatoria).filter(Convocatoria.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")
    return conv_to_dict(c, db)
