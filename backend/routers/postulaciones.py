from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import datetime
<<<<<<< HEAD
import uuid
=======
import os
import boto3
from botocore.exceptions import NoCredentialsError
>>>>>>> main

from database import get_db
from models import Usuario, Convocatoria, Postulacion, Documento, Notificacion, TipoDocumento
from schemas import PostulacionRequest, PostulacionResponse
from auth import obtener_usuario_actual
<<<<<<< HEAD
from s3_service import subir_documento, eliminar_documento

router = APIRouter(prefix="/api/postulaciones", tags=["Postulaciones"])

TIPOS_POSTULACION = ["Certificado de notas", "Paz y salvo académico"]
TIPOS_VIAJE       = ["Pasaporte", "Seguro médico internacional", "Visa de estudiante", "Carta de aceptación universitaria"]

=======
from s3_service import subir_a_s3

router = APIRouter(prefix="/api/postulaciones", tags=["Postulaciones"])

>>>>>>> main
def to_response(p: Postulacion) -> PostulacionResponse:
    programa = p.estudiante.programa.nombre if p.estudiante.programa else ""
    return PostulacionResponse(
        id=p.id,
        convocatoria=p.convocatoria.titulo,
        universidad=p.convocatoria.universidad.nombre,
        pais=p.convocatoria.universidad.pais,
        estado=p.estado,
        semestre=p.semestre,
        cartaIntencion=p.carta_intencion,
        comentarioAdmin=p.comentario_admin,
        fechaPostulacion=p.fecha_postulacion,
        fechaActualizacion=p.fecha_actualizacion,
        estudiante=f"{p.estudiante.nombre} {p.estudiante.apellido}",
        estudianteEmail=p.estudiante.email,
        cedula=p.estudiante.cedula,
        celular=p.estudiante.celular,
        programa=programa,
        documentos=len(p.documentos) if p.documentos else 0
    )

# ── Mis postulaciones ────────────────────────────────────────────────────────

@router.get("/mis", response_model=List[PostulacionResponse], summary="Ver mis postulaciones")
def mis_postulaciones(db: Session = Depends(get_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return [to_response(p) for p in (
        db.query(Postulacion)
        .filter(Postulacion.estudiante_id == usuario.id)
        .order_by(Postulacion.fecha_postulacion.desc())
        .all()
    )]

# ── Crear postulación ────────────────────────────────────────────────────────

@router.post("", response_model=PostulacionResponse, summary="Crear postulación")
def postular(request: PostulacionRequest, db: Session = Depends(get_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    convocatoria = db.query(Convocatoria).filter(Convocatoria.id == request.convocatoriaId).first()
    if not convocatoria:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")
    if convocatoria.estado != "activa":
        raise HTTPException(status_code=400, detail="La convocatoria no está activa")

    existe = db.query(Postulacion).filter(
        Postulacion.estudiante_id == usuario.id,
        Postulacion.convocatoria_id == convocatoria.id
    ).first()
    if existe:
        raise HTTPException(status_code=400, detail="Ya tienes una postulación en esta convocatoria")

    nueva = Postulacion(
        estudiante_id=usuario.id,
        convocatoria_id=convocatoria.id,
        semestre=request.semestre,
        carta_intencion=request.cartaIntencion,
        estado="en_revision",
        fecha_postulacion=datetime.datetime.now(),
        fecha_actualizacion=datetime.datetime.now()
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    admins = db.query(Usuario).filter(Usuario.rol == "administrador").all()
    for admin in admins:
        db.add(Notificacion(
            usuario_id=admin.id,
            mensaje=f"Nueva postulación de {usuario.nombre} {usuario.apellido} para '{convocatoria.titulo}'",
            tipo="postulacion"
        ))
    db.commit()

    return to_response(nueva)

# ── Documentos de postulación (certificado + paz y salvo) ────────────────────

@router.post("/{id}/documentos", summary="Subir documentos de postulación")
async def subir_documentos(
    id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
    certificado: UploadFile = File(None),
    paz_y_salvo: UploadFile = File(None)
):
    return await _guardar_docs_postulacion(id, db, usuario, certificado, paz_y_salvo)

@router.put("/{id}/documentos", summary="Reemplazar documentos de postulación")
async def actualizar_documentos(
    id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
    certificado: UploadFile = File(None),
    paz_y_salvo: UploadFile = File(None)
):
    return await _guardar_docs_postulacion(id, db, usuario, certificado, paz_y_salvo)

async def _guardar_docs_postulacion(id, db, usuario, certificado, paz_y_salvo):
    postulacion = db.query(Postulacion).filter(
        Postulacion.id == id, Postulacion.estudiante_id == usuario.id
    ).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")

    archivos_subidos = []
    pares = [(certificado, TIPOS_POSTULACION[0]), (paz_y_salvo, TIPOS_POSTULACION[1])]

    for archivo, tipo_nombre in pares:
        if archivo and archivo.filename:
            if not archivo.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"{archivo.filename} debe ser PDF")

<<<<<<< HEAD
            tipo = db.query(TipoDocumento).filter(TipoDocumento.nombre == tipo_nombre).first()
            if not tipo:
                continue

            contenido = await archivo.read()

            doc_existente = db.query(Documento).filter(
=======
            # SUBIR A S3
            url_s3 = subir_a_s3(archivo, str(id))

            # Eliminar registro previo del mismo tipo en la BD si existe
            db.query(Documento).filter(
>>>>>>> main
                Documento.postulacion_id == id,
                Documento.tipo_documento_id == tipo.id
            ).first()
            if doc_existente:
                eliminar_documento(doc_existente.s3_key)
                db.delete(doc_existente)

<<<<<<< HEAD
            s3_key = f"postulaciones/{id}/tipo_{tipo.id}/{uuid.uuid4()}_{archivo.filename}"
            subir_documento(contenido, s3_key)

            db.add(Documento(
                postulacion_id=id,
                nombre_archivo=archivo.filename,
                tipo_documento_id=tipo.id,
                s3_key=s3_key,
                mimetype="application/pdf"
            ))
            archivos_subidos.append(archivo.filename)

    db.commit()
    return {"mensaje": "Documentos guardados", "archivos": archivos_subidos}

@router.get("/{id}/documentos-postulacion", summary="Estado de documentos de postulación")
def estado_docs_postulacion(id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    postulacion = db.query(Postulacion).filter(
        Postulacion.id == id, Postulacion.estudiante_id == usuario.id
    ).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")

    tipos = db.query(TipoDocumento).filter(TipoDocumento.nombre.in_(TIPOS_POSTULACION)).all()
    docs_subidos = {d.tipo_documento_id: d for d in postulacion.documentos}

    return [
        {
            "nombre": t.nombre,
            "subido": t.id in docs_subidos,
            "nombre_archivo": docs_subidos[t.id].nombre_archivo if t.id in docs_subidos else None
        }
        for t in sorted(tipos, key=lambda x: TIPOS_POSTULACION.index(x.nombre))
    ]

# ── Documentos de viaje (paso 3) ─────────────────────────────────────────────

@router.get("/{id}/documentos-viaje", summary="Estado de documentos de viaje")
def estado_docs_viaje(id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    postulacion = db.query(Postulacion).filter(
        Postulacion.id == id, Postulacion.estudiante_id == usuario.id
    ).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")

    tipos = db.query(TipoDocumento).filter(TipoDocumento.nombre.in_(TIPOS_VIAJE)).all()
    docs_subidos = {d.tipo_documento_id: d for d in postulacion.documentos}

    return [
        {
            "nombre": t.nombre,
            "subido": t.id in docs_subidos,
            "nombre_archivo": docs_subidos[t.id].nombre_archivo if t.id in docs_subidos else None
        }
        for t in sorted(tipos, key=lambda x: TIPOS_VIAJE.index(x.nombre) if x.nombre in TIPOS_VIAJE else 99)
    ]

@router.post("/{id}/documentos-viaje", summary="Subir documentos de viaje")
async def subir_docs_viaje(
    id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
    pasaporte: UploadFile = File(None),
    seguro_medico: UploadFile = File(None),
    visa: UploadFile = File(None),
    carta_aceptacion: UploadFile = File(None)
):
    postulacion = db.query(Postulacion).filter(
        Postulacion.id == id, Postulacion.estudiante_id == usuario.id
    ).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    if postulacion.estado not in ["aprobada", "docs_pendientes"]:
        raise HTTPException(status_code=400, detail="Solo puedes subir documentos de viaje si tu postulación está aprobada")

    archivos = [pasaporte, seguro_medico, visa, carta_aceptacion]
    pares = list(zip(archivos, TIPOS_VIAJE))
    archivos_subidos = []

    for archivo, tipo_nombre in pares:
        if archivo and archivo.filename:
            if not archivo.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"{archivo.filename} debe ser PDF")

            tipo = db.query(TipoDocumento).filter(TipoDocumento.nombre == tipo_nombre).first()
            if not tipo:
                continue

            contenido = await archivo.read()

            doc_existente = db.query(Documento).filter(
                Documento.postulacion_id == id,
                Documento.tipo_documento_id == tipo.id
            ).first()
            if doc_existente:
                eliminar_documento(doc_existente.s3_key)
                db.delete(doc_existente)

            s3_key = f"postulaciones/{id}/tipo_{tipo.id}/{uuid.uuid4()}_{archivo.filename}"
            subir_documento(contenido, s3_key)

            db.add(Documento(
                postulacion_id=id,
                nombre_archivo=archivo.filename,
                tipo_documento_id=tipo.id,
                s3_key=s3_key,
                mimetype="application/pdf"
            ))
            archivos_subidos.append(archivo.filename)

    if archivos_subidos and postulacion.estado == "aprobada":
        postulacion.estado = "docs_pendientes"

    db.commit()
    return {"mensaje": "Documentos de viaje guardados", "archivos": archivos_subidos}
=======
            # Guardar nueva URL en la BD
            doc = Documento(
                postulacion_id=id,
                nombre_archivo=archivo.filename,
                tipo_documento_id=tipo_id,
                s3_key=url_s3,
                fecha_subida=datetime.datetime.now()
            )
            db.add(doc)
            archivos_subidos.append(archivo.filename)

    db.commit()
    return {"mensaje": f"{len(archivos_subidos)} documento(s) subido(s) a S3 correctamente", "archivos": archivos_subidos}

DOCS_VIAJE = [
    ("vuelos",  "Tiquetes de vuelo",     3),
    ("seguro",  "Seguro médico",         4),
    ("visa",    "Visa",                  5),
    ("pasaporte","Pasaporte",            6),
]

@router.post("/{id}/documentos-viaje", summary="Subir documentos de segunda fase (viaje)")
async def subir_documentos_viaje(
    id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
    vuelos:    UploadFile = File(None),
    seguro:    UploadFile = File(None),
    visa:      UploadFile = File(None),
    pasaporte: UploadFile = File(None)
):
    """Sube los documentos de viaje (segunda fase) para una postulación aprobada."""
    postulacion = db.query(Postulacion).filter(
        Postulacion.id == id,
        Postulacion.estudiante_id == usuario.id
    ).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    if postulacion.estado not in ["aprobada", "necesita_correcciones_viaje"]:
        raise HTTPException(status_code=400, detail="Solo puedes subir documentos de viaje cuando tu postulación está aprobada o requiere correcciones de viaje")

    archivos = [vuelos, seguro, visa, pasaporte]
    subidos = []

    for archivo, (campo, nombre_tipo, tipo_id) in zip(archivos, DOCS_VIAJE):
        if archivo and archivo.filename:
            if not archivo.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"'{archivo.filename}' debe ser PDF")

            # Asegurar que el TipoDocumento existe
            tipo = db.query(TipoDocumento).filter(TipoDocumento.id == tipo_id).first()
            if not tipo:
                tipo = TipoDocumento(id=tipo_id, nombre=nombre_tipo)
                db.add(tipo)
                db.flush()

            # SUBIR A S3
            url_s3 = subir_a_s3(archivo, str(id))

            # Eliminar registro previo en la BD
            db.query(Documento).filter(
                Documento.postulacion_id == id,
                Documento.tipo_documento_id == tipo_id
            ).delete()

            # Guardar nueva URL en la BD
            db.add(Documento(
                postulacion_id=id,
                nombre_archivo=archivo.filename,
                tipo_documento_id=tipo_id,
                s3_key=url_s3,
                fecha_subida=datetime.datetime.now()
            ))
            subidos.append(archivo.filename)

    if subidos:
        postulacion.estado = "docs_viaje_enviados"
    db.commit()
    return {"mensaje": f"{len(subidos)} documento(s) de viaje subido(s) a S3", "archivos": subidos}
>>>>>>> main
