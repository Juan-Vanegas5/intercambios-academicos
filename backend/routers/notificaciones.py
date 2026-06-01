from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Notificacion
from auth import obtener_usuario_actual

router = APIRouter(prefix="/api/notificaciones", tags=["Notificaciones"])


@router.get("", summary="Obtener notificaciones del usuario autenticado")
def mis_notificaciones(db: Session = Depends(get_db), usuario=Depends(obtener_usuario_actual)):
    notifs = (
        db.query(Notificacion)
        .filter(Notificacion.usuario_id == usuario.id)
        .order_by(Notificacion.fecha.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": n.id,
            "mensaje": n.mensaje,
            "leida": n.leida,
            "fecha": n.fecha.isoformat() if n.fecha else None,
        }
        for n in notifs
    ]


@router.get("/no-leidas", summary="Cantidad de notificaciones no leídas")
def contar_no_leidas(db: Session = Depends(get_db), usuario=Depends(obtener_usuario_actual)):
    count = (
        db.query(Notificacion)
        .filter(Notificacion.usuario_id == usuario.id, Notificacion.leida == False)
        .count()
    )
    return {"no_leidas": count}


@router.put("/{id}/leer", summary="Marcar una notificación como leída")
def marcar_leida(id: int, db: Session = Depends(get_db), usuario=Depends(obtener_usuario_actual)):
    notif = (
        db.query(Notificacion)
        .filter(Notificacion.id == id, Notificacion.usuario_id == usuario.id)
        .first()
    )
    if notif:
        notif.leida = True
        db.commit()
    return {"ok": True}


@router.put("/leer-todas", summary="Marcar todas como leídas")
def marcar_todas_leidas(db: Session = Depends(get_db), usuario=Depends(obtener_usuario_actual)):
    db.query(Notificacion).filter(
        Notificacion.usuario_id == usuario.id, Notificacion.leida == False
    ).update({"leida": True})
    db.commit()
    return {"ok": True}
