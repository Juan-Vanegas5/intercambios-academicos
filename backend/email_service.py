"""
email_service.py — Envío de correos transaccionales via AWS SES.

Variables de entorno requeridas:
  SES_FROM_EMAIL   Dirección verificada en SES (ej: no-reply@intercambiosupc.lat)
  AWS_REGION       Ya configurada para S3 (ej: us-east-2)

Credenciales: en EC2 se resuelven automáticamente via IAM Role.
Para desarrollo local usar AWS CLI o variables AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY.
"""

import boto3
import random
import datetime
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

AWS_REGION     = os.getenv("AWS_REGION", "us-east-2")
SES_FROM_EMAIL = os.getenv("SES_FROM_EMAIL", "")


def _ses_client():
    return boto3.client("ses", region_name=AWS_REGION)


def _enviar_ses(destinatario: str, asunto: str, html: str) -> bool:
    """Función base: envía un correo HTML via SES."""
    if not SES_FROM_EMAIL:
        print(f"[email_service] SES_FROM_EMAIL no configurado — correo no enviado a {destinatario}")
        return True  # no bloquea el flujo en desarrollo

    try:
        _ses_client().send_email(
            Source=SES_FROM_EMAIL,
            Destination={"ToAddresses": [destinatario]},
            Message={
                "Subject": {"Data": asunto, "Charset": "UTF-8"},
                "Body":    {"Html": {"Data": html, "Charset": "UTF-8"}},
            },
        )
        return True
    except ClientError as e:
        print(f"[email_service] SES error al enviar a {destinatario}: {e}")
        return False


# ── Códigos de verificación (login y registro) ────────────────────────────────

def generar_y_guardar_codigo(email: str, db) -> str:
    """Genera un código de 6 dígitos y lo guarda en el usuario existente (para login)."""
    from models import Usuario
    codigo = str(random.randint(100000, 999999))
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario:
        usuario.verificacion_codigo  = codigo
        usuario.verificacion_expira  = datetime.datetime.now() + datetime.timedelta(minutes=10)
        db.commit()
    return codigo


def generar_y_guardar_codigo_registro(email: str, db) -> str:
    """
    Genera un código de 6 dígitos para un usuario recién creado con
    email_verificado=False (paso 1 del registro).
    """
    from models import Usuario
    codigo = str(random.randint(100000, 999999))
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario:
        usuario.verificacion_codigo = codigo
        usuario.verificacion_expira = datetime.datetime.now() + datetime.timedelta(minutes=10)
        db.commit()
    return codigo


def verificar_codigo(email: str, codigo: str, db) -> bool:
    """Valida el código de 6 dígitos (login y registro). Lo elimina al validar."""
    from models import Usuario
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario or not usuario.verificacion_codigo:
        return False
    if datetime.datetime.now() > usuario.verificacion_expira:
        usuario.verificacion_codigo = None
        usuario.verificacion_expira = None
        db.commit()
        return False
    if usuario.verificacion_codigo != codigo:
        return False
    usuario.verificacion_codigo = None
    usuario.verificacion_expira = None
    db.commit()
    return True


# ── Plantillas de correo ──────────────────────────────────────────────────────

def enviar_codigo(email: str, codigo: str, nombre: str) -> bool:
    """Envía el código de 6 dígitos para iniciar sesión (MFA de login)."""
    print(f"\n{'='*50}\n  LOGIN — código {codigo} → {email}\n{'='*50}\n")

    html = f"""
    <html>
    <body style="font-family:Arial,sans-serif;background:#f9fafb;padding:30px;">
      <div style="max-width:480px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <div style="background:#1a3a6b;padding:24px;text-align:center;">
          <h2 style="color:white;margin:0;font-size:1.3rem;">🎓 Intercambios Académicos UPC</h2>
        </div>
        <div style="padding:32px;">
          <p style="color:#374151;">Hola <strong>{nombre}</strong>,</p>
          <p style="color:#374151;">Tu código de verificación para <strong>iniciar sesión</strong> es:</p>
          <div style="background:#eff6ff;border:2px solid #2563eb;border-radius:10px;padding:24px;text-align:center;margin:24px 0;">
            <span style="font-size:2.8rem;font-weight:700;letter-spacing:10px;color:#1a3a6b;">{codigo}</span>
          </div>
          <p style="color:#6b7280;font-size:0.9rem;">⏱ Este código expira en <strong>10 minutos</strong>.</p>
          <p style="color:#6b7280;font-size:0.9rem;">Si no intentaste iniciar sesión, ignora este mensaje.</p>
        </div>
        <div style="background:#f3f4f6;padding:16px;text-align:center;">
          <p style="color:#9ca3af;font-size:0.8rem;margin:0;">Universidad Piloto de Colombia — 2026</p>
        </div>
      </div>
    </body>
    </html>
    """
    return _enviar_ses(email, "Tu código de acceso — Intercambios UPC", html)


def enviar_codigo_registro(email: str, codigo: str, nombre: str) -> bool:
    """Envía el código de 6 dígitos para verificar el correo al registrarse (MFA de registro)."""
    print(f"\n{'='*50}\n  REGISTRO — código {codigo} → {email}\n{'='*50}\n")

    html = f"""
    <html>
    <body style="font-family:Arial,sans-serif;background:#f9fafb;padding:30px;">
      <div style="max-width:480px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <div style="background:#1a3a6b;padding:24px;text-align:center;">
          <h2 style="color:white;margin:0;font-size:1.3rem;">🎓 Intercambios Académicos UPC</h2>
        </div>
        <div style="padding:32px;">
          <p style="color:#374151;">Hola <strong>{nombre}</strong>,</p>
          <p style="color:#374151;">Para completar tu registro, ingresa el siguiente código de verificación:</p>
          <div style="background:#f0fdf4;border:2px solid #16a34a;border-radius:10px;padding:24px;text-align:center;margin:24px 0;">
            <span style="font-size:2.8rem;font-weight:700;letter-spacing:10px;color:#15803d;">{codigo}</span>
          </div>
          <p style="color:#6b7280;font-size:0.9rem;">⏱ Este código expira en <strong>10 minutos</strong>.</p>
          <p style="color:#6b7280;font-size:0.9rem;">Si no intentaste crear una cuenta, ignora este mensaje.</p>
        </div>
        <div style="background:#f3f4f6;padding:16px;text-align:center;">
          <p style="color:#9ca3af;font-size:0.8rem;margin:0;">Universidad Piloto de Colombia — 2026</p>
        </div>
      </div>
    </body>
    </html>
    """
    return _enviar_ses(email, "Verifica tu correo — Intercambios UPC", html)


def enviar_aprobacion(email: str, nombre: str, convocatoria: str, comentario: str = None) -> bool:
    """Notifica al estudiante que su postulación fue aprobada."""
    print(f"\n{'='*50}\n  APROBACIÓN para {email}: {convocatoria}\n{'='*50}\n")

    comentario_html = f"""
      <div style="background:#f0fdf4;border:1px solid #16a34a;border-radius:8px;padding:12px;margin-top:12px;">
        <strong style="color:#15803d;">Comentario del administrador:</strong>
        <p style="color:#374151;margin:4px 0 0;">{comentario}</p>
      </div>""" if comentario else ""

    html = f"""
    <html>
    <body style="font-family:Arial,sans-serif;background:#f9fafb;padding:30px;">
      <div style="max-width:520px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <div style="background:#1a3a6b;padding:24px;text-align:center;">
          <h2 style="color:white;margin:0;font-size:1.3rem;">🎓 Intercambios Académicos UPC</h2>
        </div>
        <div style="padding:32px;">
          <div style="text-align:center;margin-bottom:20px;">
            <span style="font-size:3rem;">🎉</span>
          </div>
          <p style="color:#374151;">Hola <strong>{nombre}</strong>,</p>
          <p style="color:#374151;font-size:1.05rem;">
            ¡Nos complace informarte que tu postulación a
            <strong style="color:#1a3a6b;">{convocatoria}</strong> ha sido
            <strong style="color:#16a34a;">APROBADA</strong>!
          </p>
          {comentario_html}
          <div style="background:#eff6ff;border-radius:10px;padding:20px;margin:20px 0;text-align:center;">
            <p style="color:#1a3a6b;font-weight:600;margin:0 0 8px;">Próximo paso</p>
            <p style="color:#374151;font-size:0.9rem;margin:0;">
              Ingresa a la plataforma y sube tus <strong>documentos de viaje</strong>
              (pasaporte, seguro médico, visa y carta de aceptación).
            </p>
          </div>
          <div style="text-align:center;">
            <a href="https://intercambiosupc.lat/seguimiento.html"
               style="background:#1a3a6b;color:white;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;display:inline-block;">
              Ver Mis Postulaciones →
            </a>
          </div>
        </div>
        <div style="background:#f3f4f6;padding:16px;text-align:center;">
          <p style="color:#9ca3af;font-size:0.8rem;margin:0;">Universidad Piloto de Colombia — 2026</p>
        </div>
      </div>
    </body>
    </html>
    """
    return _enviar_ses(email, f"🎉 Tu postulación fue APROBADA — {convocatoria}", html)
