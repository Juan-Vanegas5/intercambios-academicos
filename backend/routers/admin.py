from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Usuario, Postulacion, Convocatoria, Documento, Universidad, Notificacion
from schemas import EstadoRequest, PostulacionResponse, DocumentoResponse, ConvocatoriaCreate
from auth import solo_admin
from routers.postulaciones import to_response

router = APIRouter(prefix="/api/admin", tags=["Administración"])


# ── utilidad interna ────────────────────────────────────────────────
def _notificar(db: Session, usuario_id: int, mensaje: str, tipo: str, url: str = None):
    """Inserta una notificación sin hacer commit (el llamador decide cuándo commitear)."""
    db.add(Notificacion(
        usuario_id=usuario_id,
        mensaje=mensaje,
        leida=False,
        tipo=tipo,
        url=url,
    ))


# ── endpoints ───────────────────────────────────────────────────────
@router.get("/postulaciones", response_model=List[PostulacionResponse],
            summary="Ver todas las postulaciones")
def todas(db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    return [to_response(p) for p in db.query(Postulacion).all()]


@router.get("/estadisticas", summary="Estadísticas generales")
def estadisticas(db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    total      = db.query(Postulacion).count()
    aprobadas  = db.query(Postulacion).filter(Postulacion.estado == "aprobada").count()
    rechazadas = db.query(Postulacion).filter(Postulacion.estado == "rechazada").count()
    revision   = db.query(Postulacion).filter(Postulacion.estado == "en_revision").count()
    return {"total": total, "aprobadas": aprobadas, "rechazadas": rechazadas, "en_revision": revision}


@router.get("/postulaciones/{id}/documentos", response_model=List[DocumentoResponse],
            summary="Listar documentos de una postulación")
def ver_documentos(id: int, db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
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
            summary="Aprobar, rechazar o comentar postulación")
def actualizar_estado(
    id: int, request: EstadoRequest,
    db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)
):
    if request.estado not in ["aprobada", "rechazada", "en_revision"]:
        raise HTTPException(status_code=400, detail="Estado inválido")

    postulacion = db.query(Postulacion).filter(Postulacion.id == id).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")

    estado_anterior = postulacion.estado
    comentario_anterior = postulacion.comentario_admin or ""
    postulacion.estado = request.estado
    postulacion.comentario_admin = request.comentario

    # ── Notificación al estudiante ──────────────────────────────────
    conv_titulo = postulacion.convocatoria.titulo if postulacion.convocatoria else f"#{id}"
    url_seguimiento = "../../pages/seguimiento.html"  # ruta relativa desde admin/

    if request.estado != estado_anterior:
        if request.estado == "aprobada":
            msg_est = f"🎉 ¡Tu postulación a «{conv_titulo}» fue APROBADA!"
            if request.comentario:
                msg_est += f" Comentario del administrador: {request.comentario}"
        elif request.estado == "rechazada":
            msg_est = f"❌ Tu postulación a «{conv_titulo}» fue rechazada."
            if request.comentario:
                msg_est += f" Motivo: {request.comentario}"
        else:
            msg_est = f"🔄 Tu postulación a «{conv_titulo}» volvió a estado «En revisión»."
            if request.comentario:
                msg_est += f" Nota: {request.comentario}"

        _notificar(db, postulacion.estudiante_id, msg_est,
                   tipo="estado_postulacion", url="seguimiento.html")

    elif request.comentario and request.comentario != comentario_anterior:
        # Sólo cambió el comentario, no el estado
        msg_est = f"💬 El administrador dejó un comentario en tu postulación a «{conv_titulo}»: {request.comentario}"
        _notificar(db, postulacion.estudiante_id, msg_est,
                   tipo="comentario", url="seguimiento.html")

    # ── Notificación al admin que hizo la acción (retroalimentación) ─
    if request.estado != estado_anterior:
        if request.estado == "aprobada":
            msg_adm = f"✔ Postulación #{id} de {postulacion.estudiante.nombre} {postulacion.estudiante.apellido} marcada como APROBADA."
        elif request.estado == "rechazada":
            msg_adm = f"✘ Postulación #{id} de {postulacion.estudiante.nombre} {postulacion.estudiante.apellido} marcada como RECHAZADA."
        else:
            msg_adm = f"🔄 Postulación #{id} de {postulacion.estudiante.nombre} {postulacion.estudiante.apellido} regresada a EN REVISIÓN."
        _notificar(db, admin.id, msg_adm, tipo="accion_admin", url="panel.html")

    elif request.comentario:
        msg_adm = f"💬 Comentario guardado en postulación #{id} de {postulacion.estudiante.nombre} {postulacion.estudiante.apellido}."
        _notificar(db, admin.id, msg_adm, tipo="accion_admin", url="panel.html")

    db.commit()
    db.refresh(postulacion)
    return to_response(postulacion)


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


@router.delete("/convocatorias/{id}", summary="Eliminar convocatoria")
def eliminar_convocatoria(id: int, db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    conv = db.query(Convocatoria).filter(Convocatoria.id == id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")
    db.delete(conv)
    db.commit()
    return {"mensaje": "Convocatoria eliminada"}