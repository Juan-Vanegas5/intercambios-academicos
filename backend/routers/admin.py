from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from typing import List

from database import get_db
<<<<<<< HEAD
from models import Usuario, Postulacion, Convocatoria, Documento, Universidad, Notificacion
from schemas import EstadoRequest, PostulacionResponse, DocumentoResponse, ConvocatoriaCreate, NotificacionResponse, SeleccionGanadoresRequest
from auth import solo_admin
from routers.postulaciones import to_response
from s3_service import generar_url_descarga, eliminar_documento
from email_service import enviar_aprobacion

router = APIRouter(prefix="/api/admin", tags=["Administración"])

ESTADOS_VALIDOS = ["aprobada", "rechazada", "en_revision", "revisando_documentos", "necesita_correcciones", "docs_pendientes", "completada"]

def _notificar(db: Session, usuario_id: int, mensaje: str, tipo: str = "general", url: str = None):
    db.add(Notificacion(usuario_id=usuario_id, mensaje=mensaje, tipo=tipo, url=url))
=======
from models import Usuario, Postulacion, Documento, Convocatoria, ProgramaAcademico, Notificacion, Universidad
from schemas import (EstadoRequest, PostulacionResponse, DocumentoResponse,
                     SeleccionGanadoresRequest, ConvocatoriaCreate, ConvocatoriaUpdate,
                     UniversidadCreate, UniversidadUpdate)
from auth import solo_admin
from routers.postulaciones import to_response
from email_service import enviar_notificacion_estado, enviar_notificacion_universidad_destino
from pdf_service import generar_certificado_pdf
from s3_service import descargar_de_s3
import datetime

router = APIRouter(prefix="/api/admin", tags=["Administración"])

ESTADOS_VALIDOS = ["aprobada", "rechazada", "en_revision", "revisando_documentos",
                   "necesita_correcciones", "docs_pendientes", "completada",
                   "docs_viaje_enviados", "necesita_correcciones_viaje"]
>>>>>>> main

# ── Postulaciones ─────────────────────────────────────────────────────────────

@router.get("/postulaciones", response_model=List[PostulacionResponse],
<<<<<<< HEAD
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

# ── Selección de ganadores por cupos ─────────────────────────────────────────

@router.get("/convocatorias/{id}/postulantes",
            summary="Ver postulantes de una convocatoria con info de cupos",
            dependencies=[Depends(solo_admin)])
def ver_postulantes_convocatoria(id: int, db: Session = Depends(get_db)):
    """
    Devuelve todas las postulaciones de una convocatoria junto con
    el total de cupos disponibles y cuántos ya han sido seleccionados.
    """
    conv = db.query(Convocatoria).filter(Convocatoria.id == id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    postulaciones = (db.query(Postulacion)
                     .filter(Postulacion.convocatoria_id == id)
                     .order_by(Postulacion.fecha_postulacion)
                     .all())
    seleccionados = sum(1 for p in postulaciones if p.estado == "aprobada")

    return {
        "convocatoria": {
            "id": conv.id,
            "titulo": conv.titulo,
            "universidad": conv.universidad.nombre if conv.universidad else "",
            "cupos": conv.cupos,
            "seleccionados": seleccionados,
            "cuposDisponibles": conv.cupos - seleccionados,
        },
        "postulaciones": [to_response(p) for p in postulaciones]
    }

@router.post("/convocatorias/{id}/seleccionar-ganadores",
             summary="Seleccionar ganadores respetando cupos")
def seleccionar_ganadores(
    id: int,
    request: SeleccionGanadoresRequest,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(solo_admin)
):
    """
    El admin envía la lista de IDs de postulaciones que quedan SELECCIONADAS.
    - Las que están en la lista → estado 'aprobada'
    - Las que NO están en la lista (y estaban en revisión) → estado 'rechazada'
    - Se valida que no supere los cupos de la convocatoria.
    """
    conv = db.query(Convocatoria).filter(Convocatoria.id == id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    if len(request.ids_seleccionados) > conv.cupos:
        raise HTTPException(
            status_code=400,
            detail=f"Solo hay {conv.cupos} cupo(s) disponible(s) pero seleccionaste {len(request.ids_seleccionados)}."
        )

    # Todas las postulaciones de esta convocatoria
    postulaciones = db.query(Postulacion).filter(Postulacion.convocatoria_id == id).all()
    ids_set = set(request.ids_seleccionados)

    for p in postulaciones:
        nuevo_estado = "aprobada" if p.id in ids_set else "rechazada"
        estado_anterior = p.estado

        if nuevo_estado == estado_anterior:
            continue

        p.estado = nuevo_estado
        conv_titulo = conv.titulo

        if nuevo_estado == "aprobada":
            msg = f"🎉 ¡Felicitaciones! Fuiste seleccionado(a) para el intercambio en «{conv_titulo}»."
            if request.comentario:
                msg += f" {request.comentario}"
            enviar_aprobacion(
                email=p.estudiante.email,
                nombre=p.estudiante.nombre,
                convocatoria=conv_titulo,
                comentario=request.comentario
            )
        else:
            msg = f"❌ Lo sentimos, no fuiste seleccionado(a) para «{conv_titulo}»."
            if request.comentario:
                msg += f" {request.comentario}"

        _notificar(db, p.estudiante_id, msg, tipo="estado_postulacion", url="seguimiento.html")

    # Notificar al admin
    _notificar(
        db, admin.id,
        f"✅ Selección de {len(ids_set)} ganador(es) completada para «{conv.titulo}».",
        tipo="accion_admin", url="panel.html"
    )

    db.commit()
    return {
        "mensaje": f"Selección completada: {len(ids_set)} aprobado(s), {len(postulaciones) - len(ids_set)} rechazado(s).",
        "aprobados": len(ids_set),
        "rechazados": len(postulaciones) - len(ids_set)
    }


@router.delete("/postulaciones/{id}", summary="Eliminar postulación de un estudiante",
               dependencies=[Depends(solo_admin)])
def eliminar_postulacion(id: int, db: Session = Depends(get_db)):
    postulacion = db.query(Postulacion).filter(Postulacion.id == id).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")

    # Eliminar documentos de S3 antes de borrar de BD
    for doc in postulacion.documentos:
        try:
            eliminar_documento(doc.s3_key)
        except Exception:
            pass
        db.delete(doc)

    # Eliminar notificaciones asociadas al estudiante de esta postulación
    db.query(Notificacion).filter(
        Notificacion.usuario_id == postulacion.estudiante_id
    ).delete()

    db.delete(postulacion)
    db.commit()
    return {"mensaje": "Postulación eliminada correctamente"}


@router.get("/postulaciones/{id}/documentos", response_model=List[DocumentoResponse],
            summary="Listar documentos de una postulación", dependencies=[Depends(solo_admin)])
def ver_documentos(id: int, db: Session = Depends(get_db)):
    if not db.query(Postulacion).filter(Postulacion.id == id).first():
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
=======
            summary="Ver todas las postulaciones")
def todas(db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    return [to_response(p) for p in db.query(Postulacion).all()]


@router.get("/postulaciones/{id}/documentos", response_model=List[DocumentoResponse],
            summary="Ver documentos de una postulación")
def ver_documentos(id: int, db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    if not db.query(Postulacion).filter(Postulacion.id == id).first():
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
>>>>>>> main
    docs = db.query(Documento).filter(Documento.postulacion_id == id).all()
    return [
        DocumentoResponse(
            id=d.id,
            nombre_archivo=d.nombre_archivo,
            tipo=d.tipo_documento.nombre if d.tipo_documento else None,
<<<<<<< HEAD
            mimetype=d.mimetype or "application/pdf",
=======
            s3_key=d.s3_key,
>>>>>>> main
            fecha_subida=d.fecha_subida
        ) for d in docs
    ]

<<<<<<< HEAD

@router.get("/documentos/{doc_id}/descargar", summary="Obtener URL de descarga desde S3")
def descargar_documento(doc_id: int, token: str = None, db: Session = Depends(get_db)):
    """
    Devuelve una URL prefirmada de S3 válida por 5 minutos.
    El navegador del admin descarga el PDF directamente desde S3, sin pasar por el backend.
    """
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
    if not doc or not doc.s3_key:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    url = generar_url_descarga(doc.s3_key, expira_segundos=300)
    return {"url": url, "nombre_archivo": doc.nombre_archivo}


@router.put("/postulaciones/{id}/estado", response_model=PostulacionResponse,
            summary="Cambiar estado de postulación")
def actualizar_estado(
    id: int, request: EstadoRequest,
    db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)
):
    if request.estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Estado inválido")
=======
>>>>>>> main

@router.put("/postulaciones/{id}/estado", response_model=PostulacionResponse,
            summary="Cambiar estado de postulación")
def actualizar_estado(id: int, request: EstadoRequest,
                      db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    if request.estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Estado inválido")
    postulacion = db.query(Postulacion).filter(Postulacion.id == id).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
<<<<<<< HEAD

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
            # Enviar email al estudiante
            enviar_aprobacion(
                email=postulacion.estudiante.email,
                nombre=postulacion.estudiante.nombre,
                convocatoria=conv_titulo,
                comentario=request.comentario
            )
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
=======
    estado_anterior = postulacion.estado
    postulacion.estado = request.estado
    postulacion.comentario_admin = request.comentario

    # Generar notificación automática al estudiante
    if request.estado != estado_anterior:
        mensajes = {
            "aprobada": "¡Felicitaciones! Tu postulación a {conv} fue APROBADA.",
            "rechazada": "Tu postulación a {conv} fue rechazada.",
            "revisando_documentos": "Estamos revisando los documentos de tu postulación a {conv}.",
            "necesita_correcciones": "Tu postulación a {conv} necesita correcciones.",
            "necesita_correcciones_viaje": "Tu postulación a {conv} requiere corrección de documentos de viaje.",
            "docs_pendientes": "Faltan documentos en tu postulación a {conv}.",
            "completada": "Tu postulación a {conv} ha sido completada.",
        }
        msg = mensajes.get(request.estado)
        if msg:
            conv_titulo = postulacion.convocatoria.titulo if postulacion.convocatoria else "la convocatoria"
            texto = msg.format(conv=conv_titulo)
            if request.comentario:
                texto += f" Comentario: {request.comentario}"
            db.add(Notificacion(
                usuario_id=postulacion.estudiante_id,
                mensaje=texto
            ))

    # Enviar correo al estudiante
    try:
        pdf_content = None
        pdf_filename = None
        
        if request.estado == "completada":
            nombre_est = f"{postulacion.estudiante.nombre} {postulacion.estudiante.apellido}"
            conv_titulo = postulacion.convocatoria.titulo if postulacion.convocatoria else "Intercambio"
            uni_nombre = postulacion.convocatoria.universidad.nombre if postulacion.convocatoria and postulacion.convocatoria.universidad else "UPC"
            pais_nombre = postulacion.convocatoria.universidad.pais if postulacion.convocatoria and postulacion.convocatoria.universidad else "Internacional"
            
            # 1. Generar certificado de intercambio
            pdf_content = generar_certificado_pdf(
                postulacion.id, 
                nombre_est, 
                conv_titulo, 
                uni_nombre, 
                pais_nombre
            )
            pdf_filename = f"Certificado_Intercambio_{postulacion.estudiante.apellido}.pdf"

            # 2. Notificar a la UNIVERSIDAD DE DESTINO
            uni_id = postulacion.convocatoria.universidad_id
            if uni_id:
                usuarios_uni = db.query(Usuario).filter(
                    Usuario.rol == "universidad",
                    Usuario.universidad_id == uni_id
                ).all()
                
                if usuarios_uni:
                    # Buscar certificado de notas (tipo_id=1)
                    doc_notas = db.query(Documento).filter(
                        Documento.postulacion_id == id,
                        Documento.tipo_documento_id == 1
                    ).first()
                    
                    attachments_uni = [
                        {'content': pdf_content, 'filename': pdf_filename}
                    ]
                    
                    if doc_notas:
                        content_notas = descargar_de_s3(doc_notas.s3_key)
                        if content_notas:
                            attachments_uni.append({
                                'content': content_notas,
                                'filename': f"Certificado_Notas_{postulacion.estudiante.apellido}.pdf"
                            })
                    
                    for u_uni in usuarios_uni:
                        enviar_notificacion_universidad_destino(
                            email_uni=u_uni.email,
                            nombre_uni=u_uni.universidad_usuario.nombre if u_uni.universidad_usuario else "Universidad de Destino",
                            nombre_est=nombre_est,
                            convocatoria=conv_titulo,
                            attachments=attachments_uni
                        )

        enviar_notificacion_estado(
            email=postulacion.estudiante.email,
            nombre=postulacion.estudiante.nombre,
            convocatoria=postulacion.convocatoria.titulo if postulacion.convocatoria else "la convocatoria",
            nuevo_estado=request.estado,
            comentario=request.comentario,
            attachment_content=pdf_content,
            attachment_filename=pdf_filename
        )
    except Exception as e:
        print(f"[admin] Error enviando email/pdf: {e}")
>>>>>>> main

    db.commit()
    db.refresh(postulacion)
    return to_response(postulacion)

<<<<<<< HEAD
# ── Convocatorias ─────────────────────────────────────────────────────────────

@router.get("/universidades", summary="Listar universidades", dependencies=[Depends(solo_admin)])
def listar_universidades(db: Session = Depends(get_db)):
    return [{"id": u.id, "nombre": u.nombre, "pais": u.pais}
            for u in db.query(Universidad).order_by(Universidad.nombre).all()]

@router.get("/convocatorias", summary="Listar todas las convocatorias (gestión)", dependencies=[Depends(solo_admin)])
def listar_convocatorias_admin(db: Session = Depends(get_db)):
    from models import Postulacion
=======



@router.delete("/postulaciones/{id}", summary="Eliminar una postulación")
def eliminar_postulacion(id: int, db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    postulacion = db.query(Postulacion).filter(Postulacion.id == id).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    db.query(Documento).filter(Documento.postulacion_id == id).delete()
    db.delete(postulacion)
    db.commit()
    return {"mensaje": "Postulación eliminada correctamente"}


# ── Estadísticas ──────────────────────────────────────────────────────────────

@router.get("/estadisticas", summary="Estadísticas generales")
def estadisticas(db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    total      = db.query(Postulacion).count()
    aprobadas  = db.query(Postulacion).filter(Postulacion.estado == "aprobada").count()
    rechazadas = db.query(Postulacion).filter(Postulacion.estado == "rechazada").count()
    en_proceso = db.query(Postulacion).filter(
        Postulacion.estado.in_(["en_revision", "revisando_documentos", "necesita_correcciones"])
    ).count()
    return {
        "total": total,
        "aprobadas": aprobadas,
        "rechazadas": rechazadas,
        "en_revision": en_proceso
    }


@router.get("/estadisticas/por-programa", summary="Postulaciones por programa académico")
def estadisticas_por_programa(db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    resultados = (
        db.query(ProgramaAcademico.nombre, func.count(Postulacion.id).label("total"))
        .join(Usuario, Usuario.programa_id == ProgramaAcademico.id)
        .join(Postulacion, Postulacion.estudiante_id == Usuario.id)
        .group_by(ProgramaAcademico.nombre)
        .order_by(func.count(Postulacion.id).desc())
        .all()
    )
    return [{"programa": r.nombre, "total": r.total} for r in resultados]


@router.get("/estadisticas/por-convocatoria", summary="Postulaciones por convocatoria")
def estadisticas_por_convocatoria(db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    resultados = (
        db.query(Convocatoria.titulo, func.count(Postulacion.id).label("total"))
        .join(Postulacion, Postulacion.convocatoria_id == Convocatoria.id)
        .group_by(Convocatoria.titulo)
        .order_by(func.count(Postulacion.id).desc())
        .limit(10)
        .all()
    )
    return [{"convocatoria": r.titulo, "total": r.total} for r in resultados]


# ── Convocatorias ─────────────────────────────────────────────────────────────

@router.get("/universidades", summary="Listar todas las universidades")
def listar_universidades(db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    return db.query(Universidad).order_by(Universidad.nombre).all()


@router.post("/universidades", summary="Agregar una nueva universidad")
def crear_universidad(request: UniversidadCreate, db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    nueva = Universidad(nombre=request.nombre, pais=request.pais)
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@router.put("/universidades/{id}", summary="Actualizar una universidad")
def actualizar_universidad(id: int, request: UniversidadUpdate, db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    u = db.query(Universidad).filter(Universidad.id == id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Universidad no encontrada")
    
    if request.nombre is not None: u.nombre = request.nombre
    if request.pais is not None: u.pais = request.pais
    
    db.commit()
    db.refresh(u)
    return u


@router.delete("/universidades/{id}", summary="Eliminar una universidad")
def eliminar_universidad(id: int, db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    u = db.query(Universidad).filter(Universidad.id == id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Universidad no encontrada")
    
    # Verificar si tiene convocatorias asociadas
    if db.query(Convocatoria).filter(Convocatoria.universidad_id == id).count() > 0:
        raise HTTPException(status_code=400, detail="No se puede eliminar una universidad que tiene convocatorias asociadas.")
        
    db.delete(u)
    db.commit()
    return {"mensaje": "Universidad eliminada correctamente"}


@router.get("/convocatorias", summary="Listar convocatorias para selección de ganadores")
def listar_convocatorias(db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
>>>>>>> main
    convs = db.query(Convocatoria).order_by(Convocatoria.fecha_creacion.desc()).all()
    return [
        {
            "id": c.id,
            "titulo": c.titulo,
            "universidad": c.universidad.nombre if c.universidad else "—",
<<<<<<< HEAD
            "pais": c.universidad.pais if c.universidad else "—",
            "ciudad": c.universidad.ciudad if c.universidad else None,
            "latitud": c.universidad.latitud if c.universidad else None,
            "longitud": c.universidad.longitud if c.universidad else None,
            "universidadId": c.universidad_id,
            "descripcion": c.descripcion,
            "requisitos": c.requisitos,
            "fechaInicio": str(c.fecha_inicio),
            "fechaCierre": str(c.fecha_cierre),
=======
            "universidad_id": c.universidad_id,
            "descripcion": c.descripcion,
            "requisitos": c.requisitos,
            "fecha_inicio": str(c.fecha_inicio),
            "fecha_cierre": str(c.fecha_cierre),
>>>>>>> main
            "cupos": c.cupos,
            "estado": c.estado,
            "totalPostulaciones": db.query(Postulacion).filter(Postulacion.convocatoria_id == c.id).count(),
        }
        for c in convs
    ]

<<<<<<< HEAD
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
=======

@router.post("/convocatorias", summary="Crear una nueva convocatoria")
def crear_convocatoria(request: ConvocatoriaCreate, db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    try:
        f_inicio = datetime.datetime.strptime(request.fecha_inicio, "%Y-%m-%d").date()
        f_cierre = datetime.datetime.strptime(request.fecha_cierre, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido (debe ser YYYY-MM-DD)")

    if f_cierre < f_inicio:
        raise HTTPException(status_code=400, detail="La fecha de cierre no puede ser anterior a la fecha de inicio")

    nueva = Convocatoria(
        titulo=request.titulo,
        universidad_id=request.universidad_id,
        descripcion=request.descripcion,
        requisitos=request.requisitos,
        fecha_inicio=f_inicio,
        fecha_cierre=f_cierre,
>>>>>>> main
        cupos=request.cupos,
        estado=request.estado,
        creado_por=admin.id
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
<<<<<<< HEAD
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
=======
    return nueva


@router.put("/convocatorias/{id}", summary="Actualizar una convocatoria")
def actualizar_convocatoria(id: int, request: ConvocatoriaUpdate, db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    c = db.query(Convocatoria).filter(Convocatoria.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    if request.titulo is not None: c.titulo = request.titulo
    if request.universidad_id is not None: c.universidad_id = request.universidad_id
    if request.descripcion is not None: c.descripcion = request.descripcion
    if request.requisitos is not None: c.requisitos = request.requisitos
    if request.cupos is not None: c.cupos = request.cupos
    if request.estado is not None: c.estado = request.estado

    try:
        if request.fecha_inicio is not None:
            c.fecha_inicio = datetime.datetime.strptime(request.fecha_inicio, "%Y-%m-%d").date()
        if request.fecha_cierre is not None:
            c.fecha_cierre = datetime.datetime.strptime(request.fecha_cierre, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido (debe ser YYYY-MM-DD)")

    # Validate dates if both are set
    fecha_inicio_final = c.fecha_inicio
    fecha_cierre_final = c.fecha_cierre
    if fecha_cierre_final < fecha_inicio_final:
        raise HTTPException(status_code=400, detail="La fecha de cierre no puede ser anterior a la fecha de inicio")

    db.commit()
    db.refresh(c)
    return c


@router.delete("/convocatorias/{id}", summary="Eliminar una convocatoria")
def eliminar_convocatoria(id: int, db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    c = db.query(Convocatoria).filter(Convocatoria.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    # Verificar si hay postulaciones asociadas
    if db.query(Postulacion).filter(Postulacion.convocatoria_id == id).count() > 0:
        raise HTTPException(status_code=400, detail="No se puede eliminar una convocatoria que ya tiene postulaciones.")

    db.delete(c)
    db.commit()
    return {"mensaje": "Convocatoria eliminada correctamente"}


@router.get("/convocatorias/{id}/postulantes",
            summary="Ver postulantes de una convocatoria con info de cupos")
def ver_postulantes(id: int, db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    conv = db.query(Convocatoria).filter(Convocatoria.id == id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    postulaciones = (db.query(Postulacion)
                     .filter(Postulacion.convocatoria_id == id)
                     .order_by(Postulacion.fecha_postulacion)
                     .all())
    seleccionados = sum(1 for p in postulaciones if p.estado == "aprobada")

    return {
        "convocatoria": {
            "id": conv.id,
            "titulo": conv.titulo,
            "universidad": conv.universidad.nombre if conv.universidad else "",
            "cupos": conv.cupos,
            "seleccionados": seleccionados,
            "cuposDisponibles": conv.cupos - seleccionados,
        },
        "postulaciones": [to_response(p) for p in postulaciones]
    }


@router.post("/convocatorias/{id}/seleccionar-ganadores",
             summary="Seleccionar ganadores respetando cupos")
def seleccionar_ganadores(id: int, request: SeleccionGanadoresRequest,
                          db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    conv = db.query(Convocatoria).filter(Convocatoria.id == id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    if len(request.ids_seleccionados) > conv.cupos:
        raise HTTPException(
            status_code=400,
            detail=f"Solo hay {conv.cupos} cupo(s) pero seleccionaste {len(request.ids_seleccionados)}."
        )

    postulaciones = db.query(Postulacion).filter(Postulacion.convocatoria_id == id).all()
    ids_set = set(request.ids_seleccionados)

    for p in postulaciones:
        nuevo_estado = "aprobada" if p.id in ids_set else "rechazada"
        if nuevo_estado != p.estado:
            p.estado = nuevo_estado
            if request.comentario:
                p.comentario_admin = request.comentario
            # Notificación automática
            if nuevo_estado == "aprobada":
                msg = f"¡Felicitaciones! Fuiste seleccionado(a) para {conv.titulo}."
            else:
                msg = f"Tu postulación a {conv.titulo} no fue seleccionada esta vez."
            if request.comentario:
                msg += f" Comentario: {request.comentario}"
            db.add(Notificacion(usuario_id=p.estudiante_id, mensaje=msg))
            
            # Enviar correo electrónico
            enviar_notificacion_estado(
                email=p.estudiante.email,
                nombre=p.estudiante.nombre,
                convocatoria=conv.titulo,
                nuevo_estado=nuevo_estado,
                comentario=request.comentario
            )

    db.commit()
    return {
        "mensaje": f"Selección completada: {len(ids_set)} aprobado(s), {len(postulaciones) - len(ids_set)} rechazado(s).",
        "aprobados": len(ids_set),
        "rechazados": len(postulaciones) - len(ids_set)
    }


# ── Gestión de usuarios ───────────────────────────────────────────────────────

@router.get("/usuarios", summary="Listar todos los usuarios")
def listar_usuarios(db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    usuarios = db.query(Usuario).order_by(Usuario.rol, Usuario.nombre).all()
    return [
        {
            "id": u.id,
            "nombre": u.nombre,
            "apellido": u.apellido,
            "email": u.email,
            "rol": u.rol,
            "es_superusuario": u.es_superusuario,
            "programa": u.programa.nombre if u.programa else None,
            "universidad_id": u.universidad_id,
            "universidad_nombre": u.universidad_usuario.nombre if u.universidad_usuario else None,
        }
        for u in usuarios
    ]


@router.put("/usuarios/{id}/superusuario", summary="Asignar o quitar superusuario")
def cambiar_superusuario(id: int, body: dict, db: Session = Depends(get_db),
                         admin: Usuario = Depends(solo_admin)):
    valor = bool(body.get("es_superusuario"))

    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Solo un administrador puede ser superusuario.
    if valor and usuario.rol != "administrador":
        raise HTTPException(
            status_code=400,
            detail="Solo un administrador puede ser superusuario."
        )

    # No permitir quitar el flag al último superusuario.
    if usuario.es_superusuario and not valor:
        otros_super = db.query(Usuario).filter(
            Usuario.es_superusuario == True, Usuario.id != id
        ).count()
        if otros_super == 0:
            raise HTTPException(
                status_code=409,
                detail="No puedes quitar el rol al último superusuario. Asigna otro primero."
            )

    usuario.es_superusuario = valor
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No puedes quitar el rol al último superusuario del sistema."
        )
    return {"mensaje": "Superusuario actualizado", "id": id, "es_superusuario": valor}


@router.put("/usuarios/{id}/rol", summary="Cambiar rol de un usuario")
def cambiar_rol(id: int, body: dict, db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    nuevo_rol = body.get("rol", "").strip()
    if nuevo_rol not in ("estudiante", "administrador", "universidad"):
        raise HTTPException(status_code=400, detail="Rol inválido.")

    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if usuario.rol == "administrador" and nuevo_rol != "administrador":
        total_admins = db.query(Usuario).filter(Usuario.rol == "administrador").count()
        if total_admins <= 1:
            raise HTTPException(
                status_code=409,
                detail="No puedes cambiar el rol del único administrador. Primero asigna otro."
            )

    usuario.rol = nuevo_rol
    if nuevo_rol == "universidad":
        usuario.universidad_id = body.get("universidad_id")
    else:
        usuario.universidad_id = None

    db.commit()
    return {"mensaje": f"Rol actualizado a '{nuevo_rol}'", "id": id, "rol": nuevo_rol}


@router.delete("/usuarios/{id}", summary="Eliminar un usuario")
def eliminar_usuario(id: int, db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if usuario.rol == "administrador":
        total_admins = db.query(Usuario).filter(Usuario.rol == "administrador").count()
        if total_admins <= 1:
            raise HTTPException(
                status_code=409,
                detail="No puedes eliminar al único administrador del sistema."
            )

    # Protección del superusuario: debe quedar siempre al menos uno.
    if usuario.es_superusuario:
        otros_super = db.query(Usuario).filter(
            Usuario.es_superusuario == True, Usuario.id != id
        ).count()
        if otros_super == 0:
            raise HTTPException(
                status_code=409,
                detail="No puedes eliminar al último superusuario. Asigna otro superusuario primero."
            )

    for postulacion in db.query(Postulacion).filter(Postulacion.estudiante_id == id).all():
        db.query(Documento).filter(Documento.postulacion_id == postulacion.id).delete()
        db.delete(postulacion)

    db.delete(usuario)
    try:
        db.commit()
    except IntegrityError:
        # Red de seguridad: el trigger de la base de datos bloqueó el borrado.
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No puedes eliminar al último superusuario del sistema."
        )
    return {"mensaje": f"Usuario '{usuario.nombre} {usuario.apellido}' eliminado correctamente"}
>>>>>>> main
