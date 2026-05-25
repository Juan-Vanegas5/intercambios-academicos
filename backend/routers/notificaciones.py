from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Notificacion, Usuario
from auth import obtener_usuario_actual
import datetime

router = APIRouter(prefix="/api/notificaciones", tags=["Notificaciones"])


@router.get("", summary="Mis notificaciones")
def mis_notificaciones(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual)
):
    notifs = (
        db.query(Notificacion)
        .filter(Notificacion.usuario_id == usuario.id)
        .order_by(Notificacion.leida.asc(), Notificacion.fecha.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id":      n.id,
            "mensaje": n.mensaje,
            "leida":   bool(n.leida),
            "tipo":    n.tipo,
            "url":     n.url,
            "fecha":   n.fecha.isoformat() if n.fecha else None,
        }
        for n in notifs
    ]


@router.put("/leer-todas", summary="Marcar todas como leídas")
def marcar_todas_leidas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual)
):
    db.query(Notificacion).filter(
        Notificacion.usuario_id == usuario.id,
        Notificacion.leida == False
    ).update({"leida": True})
    db.commit()
    return {"ok": True}


@router.put("/{id}/leer", summary="Marcar notificación como leída")
def marcar_leida(
    id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual)
):
    notif = db.query(Notificacion).filter(
        Notificacion.id == id,
        Notificacion.usuario_id == usuario.id
    ).first()
    if notif:
        notif.leida = True
        db.commit()
    return {"ok": True}