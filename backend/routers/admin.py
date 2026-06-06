from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from typing import List

from database import get_db
from models import Usuario, Postulacion, Documento, Convocatoria, ProgramaAcademico, Notificacion, Universidad
from schemas import (EstadoRequest, PostulacionResponse, DocumentoResponse,
                     SeleccionGanadoresRequest, ConvocatoriaCreate, ConvocatoriaUpdate,
                     UniversidadCreate, UniversidadUpdate)
from auth import solo_admin
from routers.postulaciones import to_response
from email_service import enviar_notificacion_estado, enviar_ficha_universidad
from pdf_service import generar_certificado_pdf, generar_ficha_estudiante_pdf
import datetime

router = APIRouter(prefix="/api/admin", tags=["Administración"])

ESTADOS_VALIDOS = ["aprobada", "rechazada", "en_revision", "revisando_documentos",
                   "necesita_correcciones", "docs_pendientes", "completada",
                   "docs_viaje_enviados", "necesita_correcciones_viaje",
                   "pendiente_verificacion_uni", "aprobada_universidad",
                   "rechazada_universidad", "docs_extra_solicitados",
                   "en_seguimiento", "seguimiento_docs_enviados", "seguimiento_completado"]

# ── Postulaciones ─────────────────────────────────────────────────────────────

@router.get("/postulaciones", response_model=List[PostulacionResponse],
            summary="Ver todas las postulaciones")
def todas(db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    return [to_response(p) for p in db.query(Postulacion).all()]


@router.get("/postulaciones/{id}/documentos", response_model=List[DocumentoResponse],
            summary="Ver documentos de una postulación")
def ver_documentos(id: int, db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    if not db.query(Postulacion).filter(Postulacion.id == id).first():
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    docs = db.query(Documento).filter(Documento.postulacion_id == id).all()
    return [
        DocumentoResponse(
            id=d.id,
            nombre_archivo=d.nombre_archivo,
            tipo=d.tipo_documento.nombre if d.tipo_documento else None,
            tipo_id=d.tipo_documento_id,
            s3_key=d.s3_key,
            fecha_subida=d.fecha_subida
        ) for d in docs
    ]


@router.put("/postulaciones/{id}/estado", response_model=PostulacionResponse,
            summary="Cambiar estado de postulación")
def actualizar_estado(id: int, request: EstadoRequest,
                      db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    if request.estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Estado inválido")
    postulacion = db.query(Postulacion).filter(Postulacion.id == id).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    estado_anterior = postulacion.estado
    import datetime as dt

    # ── Si admin aprueba → pasa a pendiente_verificacion_uni automáticamente ──
    estado_final = request.estado
    if request.estado == "aprobada":
        estado_final = "pendiente_verificacion_uni"
        postulacion.verificacion_universidad = "pendiente"

    postulacion.estado = estado_final
    postulacion.comentario_admin = request.comentario
    postulacion.fecha_actualizacion = dt.datetime.now()

    # Generar notificación automática al estudiante
    if estado_final != estado_anterior:
        mensajes = {
            "pendiente_verificacion_uni": "¡Tu postulación a {conv} fue APROBADA por el administrador! Ahora está pendiente de verificación por la universidad de destino.",
            "rechazada": "Tu postulación a {conv} fue rechazada.",
            "revisando_documentos": "Estamos revisando los documentos de tu postulación a {conv}.",
            "necesita_correcciones": "Tu postulación a {conv} necesita correcciones.",
            "necesita_correcciones_viaje": "Tu postulación a {conv} requiere corrección de documentos de viaje.",
            "docs_pendientes": "Faltan documentos en tu postulación a {conv}.",
            "completada": "¡Tu proceso de intercambio a {conv} ha sido COMPLETADO! Puedes descargar tu certificado de participación.",
            "en_seguimiento": "Tu intercambio en {conv} ha finalizado. Ahora debes subir tus documentos de seguimiento académico: certificado de notas de la universidad de destino y constancia académica.",
            "seguimiento_docs_enviados": "Tus documentos de seguimiento para {conv} están siendo revisados por el administrador.",
            "seguimiento_completado": "¡Tu proceso de intercambio académico en {conv} ha sido COMPLETADO exitosamente! Todos los documentos de seguimiento han sido revisados.",
        }
        msg = mensajes.get(estado_final)
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

        if estado_final == "completada":
            nombre_est = f"{postulacion.estudiante.nombre} {postulacion.estudiante.apellido}"
            conv_titulo = postulacion.convocatoria.titulo if postulacion.convocatoria else "Intercambio"
            uni_nombre = postulacion.convocatoria.universidad.nombre if postulacion.convocatoria and postulacion.convocatoria.universidad else "UPC"
            pais_nombre = postulacion.convocatoria.universidad.pais if postulacion.convocatoria and postulacion.convocatoria.universidad else "Internacional"

            pdf_content = generar_certificado_pdf(
                postulacion.id, nombre_est, conv_titulo, uni_nombre, pais_nombre
            )
            pdf_filename = f"Certificado_Intercambio_{postulacion.estudiante.apellido}.pdf"

        enviar_notificacion_estado(
            email=postulacion.estudiante.email,
            nombre=postulacion.estudiante.nombre,
            convocatoria=postulacion.convocatoria.titulo if postulacion.convocatoria else "la convocatoria",
            nuevo_estado=estado_final,
            comentario=request.comentario,
            attachment_content=pdf_content,
            attachment_filename=pdf_filename
        )
    except Exception as e:
        print(f"[admin] Error enviando email/pdf al estudiante: {e}")

    # ── Notificar a universidad de destino cuando pasa a pendiente_verificacion_uni ──
    if estado_final == "pendiente_verificacion_uni":
        try:
            uni_id = postulacion.convocatoria.universidad_id if postulacion.convocatoria else None
            if uni_id:
                uni_users = db.query(Usuario).filter(
                    Usuario.rol == "universidad_destino",
                    Usuario.universidad_id == uni_id
                ).all()

                if uni_users:
                    est = postulacion.estudiante
                    docs = db.query(Documento).filter(Documento.postulacion_id == postulacion.id).all()
                    docs_lista = [
                        {"tipo": d.tipo_documento.nombre if d.tipo_documento else "Documento",
                         "nombre": d.nombre_archivo}
                        for d in docs
                    ]

                    ficha_pdf = generar_ficha_estudiante_pdf(
                        postulacion_id=postulacion.id,
                        nombre=f"{est.nombre} {est.apellido}",
                        email=est.email,
                        cedula=est.cedula or "—",
                        celular=est.celular or "—",
                        codigo=est.codigo or "—",
                        programa=est.programa.nombre if est.programa else "—",
                        semestre=postulacion.semestre,
                        convocatoria=postulacion.convocatoria.titulo,
                        universidad=postulacion.convocatoria.universidad.nombre,
                        pais=postulacion.convocatoria.universidad.pais,
                        carta_intencion=postulacion.carta_intencion,
                        documentos=docs_lista,
                    )
                    ficha_filename = f"Ficha_Estudiante_{est.apellido}_{est.nombre}.pdf"

                    for uni_user in uni_users:
                        enviar_ficha_universidad(
                            email=uni_user.email,
                            nombre_uni_user=uni_user.nombre,
                            nombre_estudiante=f"{est.nombre} {est.apellido}",
                            convocatoria=postulacion.convocatoria.titulo,
                            attachment_content=ficha_pdf,
                            attachment_filename=ficha_filename,
                        )
                        db.add(Notificacion(
                            usuario_id=uni_user.id,
                            mensaje=f"Nuevo estudiante pendiente de verificación: {est.nombre} {est.apellido} — {postulacion.convocatoria.titulo}. Revisa tu panel para aprobar o rechazar."
                        ))
        except Exception as e:
            print(f"[admin] Error notificando a universidad destino: {e}")

    db.commit()
    db.refresh(postulacion)
    return to_response(postulacion)



@router.put("/postulaciones/{id}/comentario-seguimiento",
            summary="Agregar comentario de seguimiento sin cambiar estado")
def comentario_seguimiento(id: int, body: dict,
                           db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin)):
    postulacion = db.query(Postulacion).filter(Postulacion.id == id).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    comentario = body.get("comentario", "").strip()
    if not comentario:
        raise HTTPException(status_code=400, detail="El comentario no puede estar vacío")
    postulacion.comentario_admin = comentario
    postulacion.fecha_actualizacion = datetime.datetime.now()
    db.add(Notificacion(
        usuario_id=postulacion.estudiante_id,
        mensaje=f"El administrador tiene un comentario sobre tu seguimiento de {postulacion.convocatoria.titulo if postulacion.convocatoria else 'la convocatoria'}: {comentario}"
    ))
    db.commit()
    db.refresh(postulacion)
    return to_response(postulacion)


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
    convs = db.query(Convocatoria).order_by(Convocatoria.fecha_creacion.desc()).all()
    return [
        {
            "id": c.id,
            "titulo": c.titulo,
            "universidad": c.universidad.nombre if c.universidad else "—",
            "universidad_id": c.universidad_id,
            "descripcion": c.descripcion,
            "requisitos": c.requisitos,
            "fecha_inicio": str(c.fecha_inicio),
            "fecha_cierre": str(c.fecha_cierre),
            "cupos": c.cupos,
            "estado": c.estado,
            "totalPostulaciones": db.query(Postulacion).filter(Postulacion.convocatoria_id == c.id).count(),
        }
        for c in convs
    ]


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
        cupos=request.cupos,
        estado=request.estado,
        creado_por=admin.id
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
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
            "universidad": u.universidad.nombre if u.universidad else None,
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
    if nuevo_rol not in ("estudiante", "administrador", "universidad_destino"):
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
    db.commit()
    return {"mensaje": f"Rol actualizado a '{nuevo_rol}'", "id": id, "rol": nuevo_rol}


@router.put("/usuarios/{id}/universidad", summary="Asignar universidad a un usuario")
def asignar_universidad(id: int, body: dict, db: Session = Depends(get_db),
                        admin: Usuario = Depends(solo_admin)):
    universidad_id = body.get("universidad_id")
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if universidad_id:
        uni = db.query(Universidad).filter(Universidad.id == universidad_id).first()
        if not uni:
            raise HTTPException(status_code=404, detail="Universidad no encontrada")

    usuario.universidad_id = universidad_id
    db.commit()
    return {"mensaje": "Universidad asignada correctamente", "id": id,
            "universidad_id": universidad_id}


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

    # Eliminar notificaciones del usuario
    db.query(Notificacion).filter(Notificacion.usuario_id == id).delete()

    # Eliminar postulaciones y sus documentos
    for postulacion in db.query(Postulacion).filter(Postulacion.estudiante_id == id).all():
        db.query(Documento).filter(Documento.postulacion_id == postulacion.id).delete()
        db.delete(postulacion)

    # Desvincular convocatorias creadas por este usuario (no eliminarlas)
    db.query(Convocatoria).filter(Convocatoria.creado_por == id).update({"creado_por": None})

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
