from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import datetime
import os
import boto3
from botocore.exceptions import NoCredentialsError

from database import get_db
from models import Usuario, Convocatoria, Postulacion, Documento, TipoDocumento
from schemas import PostulacionRequest, PostulacionResponse
from auth import obtener_usuario_actual

router = APIRouter(prefix="/api/postulaciones", tags=["Postulaciones"])

# --- Configuración S3 ---
# Se obtienen las credenciales de las variables de entorno
S3_CLIENT = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-2")
)
BUCKET_NAME = os.getenv("AWS_S3_BUCKET", "intercambios-upc-docs")

def subir_a_s3(file: UploadFile, folder: str) -> str:
    """Sube un archivo a S3 y devuelve su URL pública."""
    s3_key = f"uploads/{folder}/{file.filename}"
    try:
        # Asegurarse de que el puntero del archivo esté al inicio
        file.file.seek(0)
        S3_CLIENT.upload_fileobj(
            file.file, 
            BUCKET_NAME, 
            s3_key,
            ExtraArgs={'ContentType': file.content_type}
        )
        # Retorna la URL del archivo en S3
        # Importante: El bucket debe tener permisos de lectura pública o usar URLs firmadas
        region = os.getenv("AWS_REGION", "us-east-2")
        return f"https://{BUCKET_NAME}.s3.{region}.amazonaws.com/{s3_key}"
    except Exception as e:
        print(f"Error subiendo a S3: {e}")
        raise HTTPException(status_code=500, detail="Error al subir archivo a la nube")

def to_response(p: Postulacion) -> PostulacionResponse:
    programa = p.estudiante.programa.nombre if p.estudiante and p.estudiante.programa else ""
    conv = p.convocatoria
    uni = conv.universidad if conv else None
    return PostulacionResponse(
        id=p.id,
        convocatoria=conv.titulo if conv else "—",
        universidad=uni.nombre if uni else "—",
        pais=uni.pais if uni else "—",
        estado=p.estado,
        semestre=p.semestre,
        cartaIntencion=p.carta_intencion,
        comentarioAdmin=p.comentario_admin,
        verificacionUniversidad=p.verificacion_universidad,
        comentarioUniversidad=p.comentario_universidad,
        fechaVerificacionUniversidad=p.fecha_verificacion_universidad,
        fechaPostulacion=p.fecha_postulacion,
        fechaActualizacion=p.fecha_actualizacion,
        estudiante=f"{p.estudiante.nombre} {p.estudiante.apellido}" if p.estudiante else "—",
        cedula=p.estudiante.cedula if p.estudiante else None,
        celular=p.estudiante.celular if p.estudiante else None,
        programa=programa,
        documentos=len(p.documentos) if p.documentos else 0
    )

@router.get("/mis", response_model=List[PostulacionResponse],
            summary="Ver mis postulaciones")
def mis_postulaciones(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual)
):
    """Devuelve las postulaciones del estudiante autenticado."""
    postulaciones = (
        db.query(Postulacion)
        .filter(Postulacion.estudiante_id == usuario.id)
        .order_by(Postulacion.fecha_postulacion.desc())
        .all()
    )
    return [to_response(p) for p in postulaciones]

@router.post("", response_model=PostulacionResponse, summary="Crear postulación")
def postular(
    request: PostulacionRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual)
):
    """El estudiante se postula a una convocatoria activa."""
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
    return to_response(nueva)

@router.post("/{id}/documentos", summary="Subir documentos PDF")
async def subir_documentos(
    id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
    certificado: UploadFile = File(None),
    paz_y_salvo: UploadFile = File(None)
):
    """Sube los documentos PDF adjuntos a una postulación del estudiante."""
    postulacion = db.query(Postulacion).filter(
        Postulacion.id == id,
        Postulacion.estudiante_id == usuario.id
    ).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")

    archivos_subidos = []
    pares = [
        (certificado, "Certificado de notas", 1),
        (paz_y_salvo, "Paz y salvo académico", 2)
    ]

    for archivo, nombre_tipo, tipo_id in pares:
        if archivo and archivo.filename:
            if not archivo.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"El archivo '{archivo.filename}' debe ser PDF")

            # SUBIR A S3
            url_s3 = subir_a_s3(archivo, str(id))

            # Eliminar registro previo del mismo tipo en la BD si existe
            db.query(Documento).filter(
                Documento.postulacion_id == id,
                Documento.tipo_documento_id == tipo_id
            ).delete()

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
    if postulacion.estado not in ["aprobada", "aprobada_universidad", "necesita_correcciones_viaje"]:
        raise HTTPException(status_code=400, detail="Solo puedes subir documentos de viaje cuando tu postulación está aprobada por la universidad o requiere correcciones de viaje")

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


@router.post("/{id}/documentos-extra", summary="Subir documentos extra solicitados por la universidad")
async def subir_documentos_extra(
    id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
    documento1: UploadFile = File(None),
    documento2: UploadFile = File(None),
    documento3: UploadFile = File(None),
):
    postulacion = db.query(Postulacion).filter(
        Postulacion.id == id,
        Postulacion.estudiante_id == usuario.id
    ).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    if postulacion.estado != "docs_extra_solicitados":
        raise HTTPException(status_code=400, detail="Esta postulación no tiene documentos extra pendientes")

    subidos = []
    for archivo in [documento1, documento2, documento3]:
        if archivo and archivo.filename:
            if not archivo.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"'{archivo.filename}' debe ser PDF")
            url_s3 = subir_a_s3(archivo, str(id))
            db.add(Documento(
                postulacion_id=id,
                nombre_archivo=archivo.filename,
                tipo_documento_id=None,
                s3_key=url_s3,
                fecha_subida=datetime.datetime.now()
            ))
            subidos.append(archivo.filename)

    if not subidos:
        raise HTTPException(status_code=400, detail="Debes subir al menos un documento")

    postulacion.estado = "pendiente_verificacion_uni"
    postulacion.verificacion_universidad = "pendiente"
    postulacion.fecha_actualizacion = datetime.datetime.now()
    db.commit()
    return {"mensaje": f"{len(subidos)} documento(s) extra enviado(s)", "archivos": subidos}


DOCS_SEGUIMIENTO = [
    ("certificado_notas", "Certificado de notas destino", 7),
    ("constancia_academica", "Constancia académica", 8),
]

@router.post("/{id}/documentos-seguimiento", summary="Subir documentos de seguimiento académico")
async def subir_documentos_seguimiento(
    id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
    certificado_notas: UploadFile = File(None),
    constancia_academica: UploadFile = File(None),
):
    postulacion = db.query(Postulacion).filter(
        Postulacion.id == id,
        Postulacion.estudiante_id == usuario.id
    ).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    if postulacion.estado != "en_seguimiento":
        raise HTTPException(status_code=400, detail="Esta postulación no está en fase de seguimiento")

    archivos = [certificado_notas, constancia_academica]
    subidos = []

    for archivo, (campo, nombre_tipo, tipo_id) in zip(archivos, DOCS_SEGUIMIENTO):
        if archivo and archivo.filename:
            if not archivo.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"'{archivo.filename}' debe ser PDF")

            tipo = db.query(TipoDocumento).filter(TipoDocumento.id == tipo_id).first()
            if not tipo:
                tipo = TipoDocumento(id=tipo_id, nombre=nombre_tipo)
                db.add(tipo)
                db.flush()

            db.query(Documento).filter(
                Documento.postulacion_id == id,
                Documento.tipo_documento_id == tipo_id
            ).delete()

            url_s3 = subir_a_s3(archivo, str(id))
            db.add(Documento(
                postulacion_id=id,
                nombre_archivo=archivo.filename,
                tipo_documento_id=tipo_id,
                s3_key=url_s3,
                fecha_subida=datetime.datetime.now()
            ))
            subidos.append(archivo.filename)

    if not subidos:
        raise HTTPException(status_code=400, detail="Debes subir al menos un documento")

    postulacion.estado = "seguimiento_docs_enviados"
    postulacion.fecha_actualizacion = datetime.datetime.now()
    db.commit()
    return {"mensaje": f"{len(subidos)} documento(s) de seguimiento enviado(s)", "archivos": subidos}
