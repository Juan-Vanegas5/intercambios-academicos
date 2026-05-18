from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import datetime

from database import get_db
from models import Usuario, Convocatoria, Postulacion, Documento
from schemas import PostulacionRequest, PostulacionResponse
from auth import obtener_usuario_actual

router = APIRouter(prefix="/api/postulaciones", tags=["Postulaciones"])

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
        cedula=p.estudiante.cedula,
        celular=p.estudiante.celular,
        programa=programa,
        documentos=len(p.documentos) if p.documentos else 0
    )

@router.get("/mis", response_model=List[PostulacionResponse])
def mis_postulaciones(db: Session = Depends(get_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    postulaciones = db.query(Postulacion).filter(Postulacion.estudiante_id == usuario.id).order_by(Postulacion.fecha_postulacion.desc()).all()
    return [to_response(p) for p in postulaciones]

@router.post("", response_model=PostulacionResponse)
def postular(request: PostulacionRequest, db: Session = Depends(get_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    convocatoria = db.query(Convocatoria).filter(Convocatoria.id == request.convocatoriaId).first()
    if not convocatoria or convocatoria.estado != "activa":
        raise HTTPException(status_code=400, detail="Convocatoria no disponible")
    
    nueva = Postulacion(
        estudiante_id=usuario.id, convocatoria_id=convocatoria.id,
        semestre=request.semestre, carta_intencion=request.cartaIntencion
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return to_response(nueva)

# ESTA ES LA FUNCIÓN QUE CAMBIAMOS COMPLETAMENTE
@router.post("/{id}/documentos")
async def subir_documentos(
    id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
    certificado: UploadFile = File(None),
    paz_y_salvo: UploadFile = File(None)
):
    postulacion = db.query(Postulacion).filter(Postulacion.id == id, Postulacion.estudiante_id == usuario.id).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")

    archivos_subidos = []
    pares = [(certificado, 1), (paz_y_salvo, 2)]

    for archivo, tipo_id in pares:
        if archivo and archivo.filename:
            if not archivo.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"El archivo {archivo.filename} debe ser PDF")

            # Leemos los bytes del archivo
            contenido_binario = await archivo.read()

            # Limpiamos si ya existía uno de ese tipo
            db.query(Documento).filter(Documento.postulacion_id == id, Documento.tipo_documento_id == tipo_id).delete()

            # Guardamos en la base de datos (campo contenido_archivo)
            doc = Documento(
                postulacion_id=id,
                nombre_archivo=archivo.filename,
                tipo_documento_id=tipo_id,
                contenido_archivo=contenido_binario
            )
            db.add(doc)
            archivos_subidos.append(archivo.filename)

    db.commit()
    return {"mensaje": "Documentos guardados en la BD", "archivos": archivos_subidos}