import random
import datetime
import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

SES_FROM_EMAIL = os.getenv("SES_FROM_EMAIL", "no-reply@intercambiosupc.lat")
AWS_REGION     = os.getenv("AWS_REGION", "us-east-2")

_codigos: dict = {}

def _ses_client():
    return boto3.client("ses", region_name=AWS_REGION)

def _send_email(to: str, subject: str, html: str) -> bool:
    print(f"\n{'='*50}\n  EMAIL → {to}\n  Asunto: {subject}\n{'='*50}\n")
    try:
        _ses_client().send_email(
            Source=SES_FROM_EMAIL,
            Destination={"ToAddresses": [to]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body":    {"Html": {"Data": html, "Charset": "UTF-8"}}
            }
        )
        return True
    except ClientError as e:
        print(f"[SES] Error: {e.response['Error']['Message']}")
        return False

def generar_y_guardar_codigo(email: str) -> str:
    codigo = str(random.randint(100000, 999999))
    _codigos[email] = {
        "codigo": codigo,
        "expira": datetime.datetime.now() + datetime.timedelta(minutes=10)
    }
    return codigo

def verificar_codigo(email: str, codigo: str) -> bool:
    entrada = _codigos.get(email)
    if not entrada:
        return False
    if datetime.datetime.now() > entrada["expira"]:
        _codigos.pop(email, None)
        return False
    if entrada["codigo"] != codigo:
        return False
    _codigos.pop(email, None)
    return True

def enviar_codigo(email: str, codigo: str, nombre: str) -> bool:
    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f9fafb;padding:30px;">
      <div style="max-width:480px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <div style="background:#1a3a6b;padding:24px;text-align:center;">
          <h2 style="color:white;margin:0;">🎓 Intercambios Académicos UPC</h2>
        </div>
        <div style="padding:32px;">
          <p style="color:#374151;">Hola <strong>{nombre}</strong>,</p>
          <p style="color:#374151;">Tu código de verificación es:</p>
          <div style="background:#eff6ff;border:2px solid #2563eb;border-radius:10px;padding:24px;text-align:center;margin:24px 0;">
            <span style="font-size:2.8rem;font-weight:700;letter-spacing:10px;color:#1a3a6b;">{codigo}</span>
          </div>
          <p style="color:#6b7280;font-size:0.9rem;">⏱ Expira en <strong>10 minutos</strong>.</p>
        </div>
        <div style="background:#f3f4f6;padding:16px;text-align:center;">
          <p style="color:#9ca3af;font-size:0.8rem;margin:0;">Universidad Piloto de Colombia — 2026</p>
        </div>
      </div>
    </body></html>"""
    return _send_email(email, "Tu código de acceso — Intercambios UPC", html)

def enviar_notificacion_estado(email: str, nombre: str, convocatoria: str,
                               nuevo_estado: str, comentario: str = None) -> bool:
    titulos = {
        "aprobada":              "¡Tu postulación fue APROBADA! 🎉",
        "rechazada":             "Actualización sobre tu postulación 📬",
        "necesita_correcciones": "Tu postulación requiere correcciones ⚠️",
        "revisando_documentos":  "Estamos revisando tus documentos 📄",
        "docs_pendientes":       "Tienes documentos pendientes 📁",
        "docs_viaje_enviados":   "Documentos de viaje recibidos ✅",
        "completada":            "¡Proceso completado! Descarga tu certificado 🏆",
    }
    colores = {
        "aprobada":   "#16a34a",
        "rechazada":  "#dc2626",
        "completada": "#16a34a",
    }
    asunto = titulos.get(nuevo_estado, "Cambio de estado en tu postulación")
    color  = colores.get(nuevo_estado, "#1a3a6b")
    estado_texto = nuevo_estado.replace("_", " ").title()

    comentario_html = f"""
      <div style="background:#fef3c7;padding:15px;border-radius:8px;margin-bottom:24px;">
        <p style="margin:0;color:#92400e;font-weight:600;">Comentario del administrador:</p>
        <p style="margin:5px 0 0;color:#78350f;">{comentario}</p>
      </div>""" if comentario else ""

    certificado_html = """
      <div style="background:#f0fdf4;border:1px solid #86efac;padding:16px;border-radius:8px;margin:16px 0;">
        <p style="margin:0;color:#166534;font-weight:600;">🏆 Tu certificado está listo</p>
        <p style="margin:6px 0 0;color:#15803d;font-size:0.9rem;">
          Ingresa a la plataforma, ve a "Mis Postulaciones" y descarga tu Certificado Oficial de Intercambio Académico.
        </p>
      </div>""" if nuevo_estado == "completada" else ""

    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f9fafb;padding:30px;">
      <div style="max-width:550px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <div style="background:#1a3a6b;padding:24px;text-align:center;">
          <h2 style="color:white;margin:0;">🎓 Intercambios Académicos UPC</h2>
        </div>
        <div style="padding:32px;">
          <p style="color:#374151;font-size:1.05rem;">Hola <strong>{nombre}</strong>,</p>
          <p style="color:#374151;">Hay una actualización en tu postulación para:</p>
          <p style="color:#1a3a6b;font-weight:700;font-size:1.15rem;margin:8px 0;">{convocatoria}</p>
          <div style="background:{color}18;border-left:5px solid {color};padding:18px;margin:20px 0;border-radius:4px;">
            <p style="margin:0;color:#374151;font-size:0.9rem;">Nuevo estado:</p>
            <strong style="font-size:1.3rem;color:{color};">{estado_texto}</strong>
          </div>
          {comentario_html}
          {certificado_html}
          <div style="text-align:center;margin-top:28px;">
            <a href="https://intercambiosupc.lat/seguimiento.html"
               style="background:#1a3a6b;color:white;padding:12px 28px;text-decoration:none;border-radius:8px;font-weight:600;display:inline-block;">
              Ver mis postulaciones →
            </a>
          </div>
        </div>
        <div style="background:#1a3a6b;padding:16px;text-align:center;">
          <p style="color:#93c5fd;font-size:0.8rem;margin:0;">Universidad Piloto de Colombia — Programa de Desarrollo Web — 2026</p>
        </div>
      </div>
    </body></html>"""

    return _send_email(email, f"{asunto} — Intercambios UPC", html)
