from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Usuario, Postulacion, Documento, Convocatoria, Notificacion
from schemas import PostulacionResponse, DocumentoResponse
from auth import solo_universidad
from routers.postulaciones import to_response
from pdf_service import generar_ficha_estudiante_pdf

router = APIRouter(prefix="/api/universidad", tags=["Universidad Destino"])


@router.get("/estudiantes",
            summary="Ver estudiantes asignados a mi universidad")
def estudiantes_asignados(db: Session = Depends(get_db),
                          uni_user: Usuario = Depends(solo_universidad)):
    """
    Devuelve las postulaciones completadas (o aprobadas) cuya convocatoria
    pertenece a la universidad vinculada a este usuario.
    """
    if not uni_user.universidad_id:
        raise HTTPException(status_code=400,
                            detail="Tu cuenta no está vinculada a ninguna universidad.")

    postulaciones = (
        db.query(Postulacion)
        .join(Convocatoria, Postulacion.convocatoria_id == Convocatoria.id)
        .filter(Convocatoria.universidad_id == uni_user.universidad_id)
        .filter(Postulacion.estado.in_(["aprobada", "completada",
                                         "docs_viaje_enviados"]))
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
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")

    # Verificar que pertenece a la universidad del usuario
    if (not postulacion.convocatoria or
            postulacion.convocatoria.universidad_id != uni_user.universidad_id):
        raise HTTPException(status_code=403, detail="No tienes acceso a esta postulación")

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
        "fechaPostulacion": str(postulacion.fecha_postulacion) if postulacion.fecha_postulacion else None,
    }


@router.get("/estudiantes/{postulacion_id}/documentos",
            response_model=List[DocumentoResponse],
            summary="Ver documentos de un estudiante")
def documentos_estudiante(postulacion_id: int,
                          db: Session = Depends(get_db),
                          uni_user: Usuario = Depends(solo_universidad)):
    postulacion = db.query(Postulacion).filter(Postulacion.id == postulacion_id).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    if (not postulacion.convocatoria or
            postulacion.convocatoria.universidad_id != uni_user.universidad_id):
        raise HTTPException(status_code=403, detail="No tienes acceso a esta postulación")

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
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    if (not postulacion.convocatoria or
            postulacion.convocatoria.universidad_id != uni_user.universidad_id):
        raise HTTPException(status_code=403, detail="No tienes acceso a esta postulación")

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


@router.get("/estadisticas", summary="Estadísticas de la universidad")
def estadisticas_universidad(db: Session = Depends(get_db),
                             uni_user: Usuario = Depends(solo_universidad)):
    if not uni_user.universidad_id:
        return {"total": 0, "aprobadas": 0, "completadas": 0, "en_proceso": 0}

    base = (
        db.query(Postulacion)
        .join(Convocatoria)
        .filter(Convocatoria.universidad_id == uni_user.universidad_id)
    )
    total = base.count()
    aprobadas = base.filter(Postulacion.estado == "aprobada").count()
    completadas = base.filter(Postulacion.estado == "completada").count()
    en_proceso = base.filter(
        Postulacion.estado.in_(["en_revision", "revisando_documentos",
                                 "docs_viaje_enviados"])
    ).count()

    return {
        "total": total,
        "aprobadas": aprobadas,
        "completadas": completadas,
        "en_proceso": en_proceso,
    }
