<<<<<<< HEAD
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
=======
import random
import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
>>>>>>> main
from dotenv import load_dotenv

load_dotenv()

<<<<<<< HEAD
AWS_REGION     = os.getenv("AWS_REGION", "us-east-2")
SES_FROM_EMAIL = os.getenv("SES_FROM_EMAIL", "")


def _ses_client():
    return boto3.client("ses", region_name=AWS_REGION)
=======
EMAIL_USER     = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_HOST     = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT     = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_FROM     = os.getenv("EMAIL_USER", "no-reply@intercambiosupc.lat")

_codigos: dict = {}

def _send_email(to: str, subject: str, html: str, attachments: list = None) -> bool:
    """
    attachments: lista de diccionarios [{'content': bytes, 'filename': str}, ...]
    """
    print(f"\n{'='*50}\n  EMAIL → {to}\n  Asunto: {subject}\n{'='*50}\n")
    if not EMAIL_USER or not EMAIL_PASSWORD:
        print("  [Sin credenciales — solo log]")
        return True
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = EMAIL_FROM
        msg["To"]      = to
        msg.attach(MIMEText(html, "html"))

        if attachments:
            for att in attachments:
                if att.get('content') and att.get('filename'):
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(att['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={att['filename']}",
                    )
                    msg.attach(part)

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, to, msg.as_string())
        print("  [Enviado OK]")
        return True
    except Exception as e:
        print(f"  [Error SMTP] {e}")
        return False

def generar_y_guardar_codigo(email: str) -> str:
    codigo = str(random.randint(100000, 999999))
    _codigos[email] = {
        "codigo": codigo,
        "expira": datetime.datetime.now() + datetime.timedelta(minutes=10)
    }
    return codigo
>>>>>>> main


<<<<<<< HEAD
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
=======
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
                               nuevo_estado: str, comentario: str = None,
                               attachment_content: bytes = None, attachment_filename: str = None) -> bool:
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

    attachments = []
    if attachment_content and attachment_filename:
        attachments.append({'content': attachment_content, 'filename': attachment_filename})

    return _send_email(email, f"{asunto} — Intercambios UPC", html, attachments)

def enviar_notificacion_universidad_destino(email_uni: str, nombre_uni: str, nombre_est: str, 
                                          convocatoria: str, attachments: list) -> bool:
    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f9fafb;padding:30px;">
      <div style="max-width:550px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <div style="background:#1a3a6b;padding:24px;text-align:center;">
          <h2 style="color:white;margin:0;">🎓 Notificación de Intercambio — UPC</h2>
        </div>
        <div style="padding:32px;">
          <p style="color:#374151;font-size:1.05rem;">Estimados representantes de <strong>{nombre_uni}</strong>,</p>
          <p style="color:#374151;">Les informamos que el proceso de intercambio para el siguiente estudiante ha sido <strong>completado exitosamente</strong>:</p>
          <div style="background:#f3f4f6;padding:20px;border-radius:8px;margin:20px 0;">
            <p style="margin:0;color:#374151;"><strong>Estudiante:</strong> {nombre_est}</p>
            <p style="margin:5px 0 0;color:#374151;"><strong>Convocatoria:</strong> {convocatoria}</p>
            <p style="margin:5px 0 0;color:#374151;"><strong>Origen:</strong> Universidad Piloto de Colombia</p>
          </div>
          <p style="color:#374151;">Adjunto encontrarán:</p>
          <ul style="color:#374151;">
            <li>Certificado de Notas del estudiante.</li>
            <li>Certificado Oficial de Intercambio Académico.</li>
          </ul>
          <p style="color:#374151;">El estudiante se pondrá en contacto con ustedes pronto para los trámites finales de llegada.</p>
        </div>
        <div style="background:#1a3a6b;padding:16px;text-align:center;">
          <p style="color:#93c5fd;font-size:0.8rem;margin:0;">Oficina de Relaciones Internacionales — Universidad Piloto de Colombia</p>
        </div>
      </div>
    </body></html>"""
    return _send_email(email_uni, f"Nuevo Estudiante de Intercambio: {nombre_est}", html, attachments)
>>>>>>> main
