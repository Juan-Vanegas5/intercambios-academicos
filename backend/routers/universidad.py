from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List
import datetime

from database import get_db
from models import Usuario, Postulacion, Documento, Convocatoria, Notificacion
from schemas import PostulacionResponse, DocumentoResponse
from auth import solo_universidad
from routers.postulaciones import to_response
from pdf_service import generar_ficha_estudiante_pdf

router = APIRouter(prefix="/api/universidad", tags=["Universidad Destino"])

# Estados que la universidad puede ver
ESTADOS_VISIBLES_UNI = [
    "aprobada", "pendiente_verificacion_uni", "aprobada_universidad",
    "rechazada_universidad", "docs_extra_solicitados",
    "completada", "docs_viaje_enviados"
]


def _verificar_acceso(postulacion, uni_user):
    """Verifica que la postulación pertenece a la universidad del usuario."""
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    if (not postulacion.convocatoria or
            postulacion.convocatoria.universidad_id != uni_user.universidad_id):
        raise HTTPException(status_code=403, detail="No tienes acceso a esta postulación")


@router.get("/estudiantes",
            summary="Ver estudiantes asignados a mi universidad")
def estudiantes_asignados(db: Session = Depends(get_db),
                          uni_user: Usuario = Depends(solo_universidad)):
    if not uni_user.universidad_id:
        raise HTTPException(status_code=400,
                            detail="Tu cuenta no está vinculada a ninguna universidad.")

    postulaciones = (
        db.query(Postulacion)
        .join(Convocatoria, Postulacion.convocatoria_id == Convocatoria.id)
        .filter(Convocatoria.universidad_id == uni_user.universidad_id)
        .filter(Postulacion.estado.in_(ESTADOS_VISIBLES_UNI))
        .order_by(Postulacion.fecha_actualizacion.desc())
        .all()
    )
    return [to_response(p) for p in postulaciones]


@router.get("/estudiantes/{postulacion_id}",
            summary="Detalle de un estudiante asignado")
def detalle_estudiante(postulacion_id: int,
                       db: Session = Depends(get_db),
                       uni_user: Usuario = Depends(solo_universidad)):
    postulacion = db.query(Postulacion).filter(Postulacion.id == postulacion_id).first()
    _verificar_acceso(postulacion, uni_user)

    est = postulacion.estudiante
    return {
        "id": postulacion.id,
        "estudiante": {
            "nombre": est.nombre,
            "apellido": est.apellido,
            "email": est.email,
            "cedula": est.cedula,
            "celular": est.celular,
            "codigo": est.codigo,
            "programa": est.programa.nombre if est.programa else None,
        },
        "convocatoria": postulacion.convocatoria.titulo if postulacion.convocatoria else "",
        "semestre": postulacion.semestre,
        "estado": postulacion.estado,
        "cartaIntencion": postulacion.carta_intencion,
        "comentarioAdmin": postulacion.comentario_admin,
        "verificacionUniversidad": postulacion.verificacion_universidad,
        "comentarioUniversidad": postulacion.comentario_universidad,
        "fechaVerificacionUniversidad": str(postulacion.fecha_verificacion_universidad) if postulacion.fecha_verificacion_universidad else None,
        "fechaPostulacion": str(postulacion.fecha_postulacion) if postulacion.fecha_postulacion else None,
    }


@router.get("/estudiantes/{postulacion_id}/documentos",
            response_model=List[DocumentoResponse],
            summary="Ver documentos de un estudiante")
def documentos_estudiante(postulacion_id: int,
                          db: Session = Depends(get_db),
                          uni_user: Usuario = Depends(solo_universidad)):
    postulacion = db.query(Postulacion).filter(Postulacion.id == postulacion_id).first()
    _verificar_acceso(postulacion, uni_user)

    docs = db.query(Documento).filter(Documento.postulacion_id == postulacion_id).all()
    return [
        DocumentoResponse(
            id=d.id,
            nombre_archivo=d.nombre_archivo,
            tipo=d.tipo_documento.nombre if d.tipo_documento else None,
            s3_key=d.s3_key,
            fecha_subida=d.fecha_subida
        ) for d in docs
    ]


@router.get("/estudiantes/{postulacion_id}/ficha-pdf",
            summary="Descargar ficha PDF del estudiante")
def descargar_ficha_pdf(postulacion_id: int,
                        db: Session = Depends(get_db),
                        uni_user: Usuario = Depends(solo_universidad)):
    postulacion = db.query(Postulacion).filter(Postulacion.id == postulacion_id).first()
    _verificar_acceso(postulacion, uni_user)

    est = postulacion.estudiante
    docs = db.query(Documento).filter(Documento.postulacion_id == postulacion_id).all()
    docs_lista = [
        {"tipo": d.tipo_documento.nombre if d.tipo_documento else "Documento",
         "nombre": d.nombre_archivo}
        for d in docs
    ]

    pdf_bytes = generar_ficha_estudiante_pdf(
        postulacion_id=postulacion.id,
        nombre=f"{est.nombre} {est.apellido}",
        email=est.email,
        cedula=est.cedula or "—",
        celular=est.celular or "—",
        codigo=est.codigo or "—",
        programa=est.programa.nombre if est.programa else "—",
        semestre=postulacion.semestre,
        convocatoria=postulacion.convocatoria.titulo if postulacion.convocatoria else "",
        universidad=postulacion.convocatoria.universidad.nombre if postulacion.convocatoria and postulacion.convocatoria.universidad else "",
        pais=postulacion.convocatoria.universidad.pais if postulacion.convocatoria and postulacion.convocatoria.universidad else "",
        carta_intencion=postulacion.carta_intencion,
        documentos=docs_lista,
    )

    filename = f"Ficha_Estudiante_{est.apellido}_{est.nombre}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ── VERIFICACIÓN POR UNIVERSIDAD ─────────────────────────────────────────────

@router.put("/estudiantes/{postulacion_id}/verificar",
            summary="Aprobar o rechazar un estudiante")
def verificar_estudiante(postulacion_id: int, body: dict,
                         db: Session = Depends(get_db),
                         uni_user: Usuario = Depends(solo_universidad)):
    """
    La universidad aprueba o rechaza al estudiante.
    body: { "accion": "aprobar" | "rechazar", "comentario": "..." }
    Si aprueba → estado pasa a 'completada' (ambas partes aprobaron).
    Si rechaza → estado pasa a 'rechazada_universidad'.
    """
    postulacion = db.query(Postulacion).filter(Postulacion.id == postulacion_id).first()
    _verificar_acceso(postulacion, uni_user)

    if postulacion.estado not in ("pendiente_verificacion_uni", "docs_extra_solicitados"):
        raise HTTPException(status_code=400,
                            detail="Esta postulación no está pendiente de verificación universitaria.")

    accion = body.get("accion", "").strip().lower()
    comentario = body.get("comentario", "").strip()

    if accion not in ("aprobar", "rechazar"):
        raise HTTPException(status_code=400, detail="Acción inválida. Usa 'aprobar' o 'rechazar'.")

    postulacion.comentario_universidad = comentario
    postulacion.fecha_verificacion_universidad = datetime.datetime.now()

    est = postulacion.estudiante
    conv_titulo = postulacion.convocatoria.titulo if postulacion.convocatoria else "la convocatoria"

    if accion == "aprobar":
        postulacion.verificacion_universidad = "aprobada"
        postulacion.estado = "aprobada_universidad"

        # Notificar al estudiante
        msg = f"¡La universidad de destino APROBÓ tu postulación para {conv_titulo}! Ya puedes subir tus documentos de viaje."
        if comentario:
            msg += f" Comentario: {comentario}"
        db.add(Notificacion(usuario_id=est.id, mensaje=msg))

        # Notificar a los admins
        admins = db.query(Usuario).filter(Usuario.rol == "administrador").all()
        for admin in admins:
            db.add(Notificacion(
                usuario_id=admin.id,
                mensaje=f"La universidad de destino APROBÓ a {est.nombre} {est.apellido} para {conv_titulo}. El estudiante debe subir documentos de viaje."
            ))

    else:  # rechazar
        postulacion.verificacion_universidad = "rechazada"
        postulacion.estado = "rechazada_universidad"

        msg = f"Tu postulación a {conv_titulo} fue rechazada por la universidad de destino."
        if comentario:
            msg += f" Motivo: {comentario}"
        db.add(Notificacion(usuario_id=est.id, mensaje=msg))

        admins = db.query(Usuario).filter(Usuario.rol == "administrador").all()
        for admin in admins:
            db.add(Notificacion(
                usuario_id=admin.id,
                mensaje=f"La universidad de destino RECHAZÓ a {est.nombre} {est.apellido} para {conv_titulo}. Motivo: {comentario or 'Sin comentario'}"
            ))

    postulacion.fecha_actualizacion = datetime.datetime.now()
    db.commit()
    db.refresh(postulacion)
    return to_response(postulacion)


@router.put("/estudiantes/{postulacion_id}/solicitar-documentos",
            summary="Solicitar documentos extra al estudiante")
def solicitar_documentos_extra(postulacion_id: int, body: dict,
                               db: Session = Depends(get_db),
                               uni_user: Usuario = Depends(solo_universidad)):
    """
    La universidad solicita documentos adicionales al estudiante.
    body: { "comentario": "Necesitamos certificado de vacunación..." }
    """
    postulacion = db.query(Postulacion).filter(Postulacion.id == postulacion_id).first()
    _verificar_acceso(postulacion, uni_user)

    if postulacion.estado not in ("pendiente_verificacion_uni", "docs_extra_solicitados"):
        raise HTTPException(status_code=400,
                            detail="Esta postulación no está en un estado que permita solicitar documentos.")

    comentario = body.get("comentario", "").strip()
    if not comentario:
        raise HTTPException(status_code=400, detail="Debes especificar qué documentos necesitas.")

    postulacion.verificacion_universidad = "docs_extra"
    postulacion.estado = "docs_extra_solicitados"
    postulacion.comentario_universidad = comentario
    postulacion.fecha_verificacion_universidad = datetime.datetime.now()
    postulacion.fecha_actualizacion = datetime.datetime.now()

    est = postulacion.estudiante
    conv_titulo = postulacion.convocatoria.titulo if postulacion.convocatoria else "la convocatoria"

    db.add(Notificacion(
        usuario_id=est.id,
        mensaje=f"La universidad de destino solicita documentos adicionales para tu postulación a {conv_titulo}: {comentario}"
    ))

    # Notificar admins
    admins = db.query(Usuario).filter(Usuario.rol == "administrador").all()
    for admin in admins:
        db.add(Notificacion(
            usuario_id=admin.id,
            mensaje=f"La universidad de destino solicitó documentos extra a {est.nombre} {est.apellido} para {conv_titulo}: {comentario}"
        ))

    db.commit()
    db.refresh(postulacion)
    return to_response(postulacion)


@router.put("/estudiantes/{postulacion_id}/comentar",
            summary="Agregar comentario sin cambiar estado")
def comentar_estudiante(postulacion_id: int, body: dict,
                        db: Session = Depends(get_db),
                        uni_user: Usuario = Depends(solo_universidad)):
    """
    La universidad deja un comentario/observación sin cambiar el estado.
    body: { "comentario": "..." }
    """
    postulacion = db.query(Postulacion).filter(Postulacion.id == postulacion_id).first()
    _verificar_acceso(postulacion, uni_user)

    comentario = body.get("comentario", "").strip()
    if not comentario:
        raise HTTPException(status_code=400, detail="El comentario no puede estar vacío.")

    postulacion.comentario_universidad = comentario
    postulacion.fecha_verificacion_universidad = datetime.datetime.now()
    db.commit()
    db.refresh(postulacion)
    return {"mensaje": "Comentario guardado", "comentario": comentario}


# ── ESTADÍSTICAS ─────────────────────────────────────────────────────────────

@router.get("/estadisticas", summary="Estadísticas de la universidad")
def estadisticas_universidad(db: Session = Depends(get_db),
                             uni_user: Usuario = Depends(solo_universidad)):
    if not uni_user.universidad_id:
        return {"total": 0, "pendientes": 0, "aprobadas_uni": 0,
                "rechazadas_uni": 0, "completadas": 0, "docs_extra": 0}

    base = (
        db.query(Postulacion)
        .join(Convocatoria)
        .filter(Convocatoria.universidad_id == uni_user.universidad_id)
        .filter(Postulacion.estado.in_(ESTADOS_VISIBLES_UNI))
    )
    total = base.count()
    pendientes = base.filter(Postulacion.estado == "pendiente_verificacion_uni").count()
    aprobadas_uni = base.filter(Postulacion.estado.in_(["aprobada_universidad", "completada"])).count()
    rechazadas_uni = base.filter(Postulacion.estado == "rechazada_universidad").count()
    completadas = base.filter(Postulacion.estado == "completada").count()
    docs_extra = base.filter(Postulacion.estado == "docs_extra_solicitados").count()

    return {
        "total": total,
        "pendientes": pendientes,
        "aprobadas_uni": aprobadas_uni,
        "rechazadas_uni": rechazadas_uni,
        "completadas": completadas,
        "docs_extra": docs_extra,
    }
