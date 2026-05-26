import smtplib
import random
import datetime
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER     = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_HOST     = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT     = int(os.getenv("EMAIL_PORT", "587"))


def generar_y_guardar_codigo(email: str, db) -> str:
    from models import Usuario
    codigo = str(random.randint(100000, 999999))
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario:
        usuario.verificacion_codigo = codigo
        usuario.verificacion_expira = datetime.datetime.now() + datetime.timedelta(minutes=10)
        db.commit()
    return codigo


def verificar_codigo(email: str, codigo: str, db) -> bool:
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


def enviar_aprobacion(email: str, nombre: str, convocatoria: str, comentario: str = None) -> bool:
    print(f"\n{'='*50}")
    print(f"  APROBACIÓN para {email}: {convocatoria}")
    print(f"{'='*50}\n")

    if not EMAIL_USER or not EMAIL_PASSWORD:
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🎉 Tu postulación fue APROBADA — {convocatoria}"
        msg["From"]    = EMAIL_USER
        msg["To"]      = email

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
                <strong style="color:#1a3a6b;">{convocatoria}</strong> ha sido <strong style="color:#16a34a;">APROBADA</strong>!
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

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, email, msg.as_string())

        return True

    except Exception as e:
        print(f"[email_service] No se pudo enviar aprobación a {email}: {e}")
        return True


def enviar_codigo(email: str, codigo: str, nombre: str) -> bool:
    print(f"\n{'='*50}")
    print(f"  CÓDIGO para {email}: {codigo}")
    print(f"{'='*50}\n")

    if not EMAIL_USER or not EMAIL_PASSWORD:
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Tu código de acceso — Intercambios UPC"
        msg["From"]    = EMAIL_USER
        msg["To"]      = email

        html = f"""
        <html>
        <body style="font-family:Arial,sans-serif;background:#f9fafb;padding:30px;">
          <div style="max-width:480px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
            <div style="background:#1a3a6b;padding:24px;text-align:center;">
              <h2 style="color:white;margin:0;font-size:1.3rem;">🎓 Intercambios Académicos UPC</h2>
            </div>
            <div style="padding:32px;">
              <p style="color:#374151;">Hola <strong>{nombre}</strong>,</p>
              <p style="color:#374151;">Tu código de verificación para iniciar sesión es:</p>
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

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, email, msg.as_string())

        return True

    except Exception as e:
        print(f"[email_service] No se pudo enviar a {email}: {e}")
        return True
