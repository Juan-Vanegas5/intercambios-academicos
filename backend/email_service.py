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

# Almacén temporal en memoria: { email: { "codigo": "123456", "expira": datetime } }
_codigos: dict = {}

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
    # Sin credenciales configuradas → mostrar código en la terminal (modo desarrollo)
    if not EMAIL_USER or not EMAIL_PASSWORD:
        print(f"\n{'='*50}")
        print(f"  CÓDIGO DE VERIFICACIÓN para {email}")
        print(f"  Código: {codigo}")
        print(f"{'='*50}\n")
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
        print(f"[email_service] Error al enviar correo: {e}")
        return False
