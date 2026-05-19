from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Usuario, Postulacion, Convocatoria, Documento, Universidad, Notificacion
from schemas import EstadoRequest, PostulacionResponse, DocumentoResponse, ConvocatoriaCreate, NotificacionResponse
from auth import solo_admin
from routers.postulaciones import to_response

router = APIRouter(prefix="/api/admin", tags=["Administración"])

ESTADOS_VALIDOS = ["aprobada", "rechazada", "en_revision", "revisando_documentos", "necesita_correcciones"]

# ── Postulaciones ─────────────────────────────────────────────────────────────

@router.get("/postulaciones", response_model=List[PostulacionResponse],
            summary="Ver todas las postulaciones", dependencies=[Depends(solo_admin)])
def todas(db: Session = Depends(get_db)):
    return [to_response(p) for p in db.query(Postulacion).all()]

@router.get("/estadisticas", summary="Estadísticas generales", dependencies=[Depends(solo_admin)])
def estadisticas(db: Session = Depends(get_db)):
    total      = db.query(Postulacion).count()
    aprobadas  = db.query(Postulacion).filter(Postulacion.estado == "aprobada").count()
    rechazadas = db.query(Postulacion).filter(Postulacion.estado == "rechazada").count()
    revision   = db.query(Postulacion).filter(Postulacion.estado == "en_revision").count()
    revisando  = db.query(Postulacion).filter(Postulacion.estado == "revisando_documentos").count()
    correcciones = db.query(Postulacion).filter(Postulacion.estado == "necesita_correcciones").count()
    return {
        "total": total,
        "aprobadas": aprobadas,
        "rechazadas": rechazadas,
        "en_revision": revision + revisando + correcciones
    }

@router.get("/postulaciones/{id}/documentos", response_model=List[DocumentoResponse],
            summary="Listar documentos de una postulación", dependencies=[Depends(solo_admin)])
def ver_documentos(id: int, db: Session = Depends(get_db)):
    if not db.query(Postulacion).filter(Postulacion.id == id).first():
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    docs = db.query(Documento).filter(Documento.postulacion_id == id).all()
    return [
        DocumentoResponse(
            id=d.id,
            nombre_archivo=d.nombre_archivo,
            tipo=d.tipo_documento.nombre if d.tipo_documento else None,
            mimetype=d.mimetype or "application/pdf",
            fecha_subida=d.fecha_subida
        ) for d in docs
    ]

@router.get("/documentos/{doc_id}/descargar", summary="Descargar documento (binario desde BD)")
def descargar_documento(doc_id: int, token: str = None, db: Session = Depends(get_db)):
    from jose import jwt, JWTError
    from auth import JWT_SECRET, ALGORITHM
    if not token:
        raise HTTPException(status_code=401, detail="Token requerido")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        rol = payload.get("rol")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o vencido")
    if rol != "administrador":
        raise HTTPException(status_code=403, detail="Solo administradores")
    doc = db.query(Documento).filter(Documento.id == doc_id).first()
    if not doc or not doc.contenido_archivo:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return Response(
        content=doc.contenido_archivo,
        media_type=doc.mimetype or "application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{doc.nombre_archivo}"'}
    )

@router.put("/postulaciones/{id}/estado", response_model=PostulacionResponse,
            summary="Cambiar estado de postulación")
def actualizar_estado(
    id: int, request: EstadoRequest,
    db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)
):
    if request.estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Estado inválido")
    postulacion = db.query(Postulacion).filter(Postulacion.id == id).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    postulacion.estado = request.estado
    postulacion.comentario_admin = request.comentario
    db.commit()
    db.refresh(postulacion)
    return to_response(postulacion)

# ── Convocatorias ─────────────────────────────────────────────────────────────

@router.get("/universidades", summary="Listar universidades", dependencies=[Depends(solo_admin)])
def listar_universidades(db: Session = Depends(get_db)):
    return [{"id": u.id, "nombre": u.nombre, "pais": u.pais}
            for u in db.query(Universidad).order_by(Universidad.nombre).all()]

@router.get("/convocatorias", summary="Listar todas las convocatorias (gestión)", dependencies=[Depends(solo_admin)])
def listar_convocatorias_admin(db: Session = Depends(get_db)):
    convs = db.query(Convocatoria).order_by(Convocatoria.fecha_creacion.desc()).all()
    return [
        {
            "id": c.id,
            "titulo": c.titulo,
            "universidad": c.universidad.nombre if c.universidad else "—",
            "pais": c.universidad.pais if c.universidad else "—",
            "universidadId": c.universidad_id,
            "descripcion": c.descripcion,
            "requisitos": c.requisitos,
            "fechaInicio": str(c.fecha_inicio),
            "fechaCierre": str(c.fecha_cierre),
            "cupos": c.cupos,
            "estado": c.estado,
        }
        for c in convs
    ]

@router.post("/convocatorias", summary="Crear convocatoria")
def crear_convocatoria(request: ConvocatoriaCreate, db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    universidad = db.query(Universidad).filter(Universidad.id == request.universidadId).first()
    if not universidad:
        raise HTTPException(status_code=404, detail="Universidad no encontrada")
    nueva = Convocatoria(
        titulo=request.titulo,
        universidad_id=request.universidadId,
        descripcion=request.descripcion,
        requisitos=request.requisitos,
        fecha_inicio=request.fechaInicio,
        fecha_cierre=request.fechaCierre,
        cupos=request.cupos,
        estado=request.estado,
        creado_por=admin.id
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return {"id": nueva.id, "titulo": nueva.titulo}

@router.put("/convocatorias/{id}", summary="Editar convocatoria", dependencies=[Depends(solo_admin)])
def editar_convocatoria(id: int, request: ConvocatoriaCreate, db: Session = Depends(get_db)):
    conv = db.query(Convocatoria).filter(Convocatoria.id == id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")
    universidad = db.query(Universidad).filter(Universidad.id == request.universidadId).first()
    if not universidad:
        raise HTTPException(status_code=404, detail="Universidad no encontrada")
    conv.titulo         = request.titulo
    conv.universidad_id = request.universidadId
    conv.descripcion    = request.descripcion
    conv.requisitos     = request.requisitos
    conv.fecha_inicio   = request.fechaInicio
    conv.fecha_cierre   = request.fechaCierre
    conv.cupos          = request.cupos
    conv.estado         = request.estado
    db.commit()
    return {"id": conv.id, "titulo": conv.titulo}

@router.delete("/convocatorias/{id}", summary="Eliminar convocatoria", dependencies=[Depends(solo_admin)])
def eliminar_convocatoria(id: int, db: Session = Depends(get_db)):
    conv = db.query(Convocatoria).filter(Convocatoria.id == id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")
    db.delete(conv)
    db.commit()
    return {"mensaje": "Convocatoria eliminada"}

# ── Notificaciones ────────────────────────────────────────────────────────────

@router.get("/notificaciones", response_model=List[NotificacionResponse],
            summary="Obtener notificaciones del admin")
def obtener_notificaciones(db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    notifs = (db.query(Notificacion)
              .filter(Notificacion.usuario_id == admin.id)
              .order_by(Notificacion.fecha.desc())
              .limit(30)
              .all())
    return [
        NotificacionResponse(
            id=n.id,
            mensaje=n.mensaje,
            leida=n.leida,
            fecha=n.fecha,
            tipo=n.tipo or "postulacion"
        ) for n in notifs
    ]

@router.put("/notificaciones/leidas", summary="Marcar todas las notificaciones como leídas")
def marcar_leidas(db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    (db.query(Notificacion)
     .filter(Notificacion.usuario_id == admin.id, Notificacion.leida == False)
     .update({"leida": True}))
    db.commit()
    return {"mensaje": "Notificaciones marcadas como leídas"}
