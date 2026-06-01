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

    # Siempre mostrar en terminal (útil para cuentas de prueba sin correo real)
    print(f"\n{'='*50}")
    print(f"  CÓDIGO para {email}: {codigo}")
    print(f"{'='*50}\n")

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
        return True  # El código ya se imprimió en terminal, el login puede continuar

def enviar_notificacion_estado(email: str, nombre: str, convocatoria: str, nuevo_estado: str, comentario: str = None) -> bool:
    """Envía un correo al estudiante cuando cambia el estado de su postulación."""
    
    # Textos según el estado
    titulos = {
        "aprobada": "¡Tu postulación ha sido APROBADA! 🥳",
        "rechazada": "Actualización sobre tu postulación 📬",
        "necesita_correcciones": "Tu postulación requiere correcciones ⚠️",
        "revisando_documentos": "Estamos revisando tus documentos 📄",
        "docs_pendientes": "Tienes documentos pendientes 📁"
    }
    
    colores = {
        "aprobada": "#16a34a",
        "rechazada": "#dc2626",
        "necesita_correcciones": "#d97706",
        "default": "#1a3a6b"
    }

    asunto = titulos.get(nuevo_estado, "Cambio de estado en tu postulación")
    color = colores.get(nuevo_estado, colores["default"])
    estado_texto = nuevo_estado.replace("_", " ").capitalize()

    # Log en terminal para desarrollo
    print(f"\n{'='*50}")
    print(f"  EMAIL NOTIFICACIÓN para {email}")
    print(f"  Estado: {estado_texto}")
    print(f"  Convocatoria: {convocatoria}")
    print(f"{'='*50}\n")

    if not EMAIL_USER or not EMAIL_PASSWORD:
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{asunto} — Intercambios UPC"
        msg["From"]    = EMAIL_USER
        msg["To"]      = email

        html = f"""
        <html>
        <body style="font-family:Arial,sans-serif;background:#f9fafb;padding:30px;">
          <div style="max-width:550px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
            <div style="background:#1a3a6b;padding:24px;text-align:center;">
              <h2 style="color:white;margin:0;font-size:1.3rem;">🎓 Intercambios Académicos UPC</h2>
            </div>
            <div style="padding:32px;">
              <p style="color:#374151;font-size:1.1rem;">Hola <strong>{nombre}</strong>,</p>
              <p style="color:#374151;">Hay una actualización importante en tu proceso de intercambio para:</p>
              <p style="color:#1a3a6b;font-weight:700;font-size:1.2rem;margin:10px 0;">{convocatoria}</p>
              
              <div style="background:{color}10;border-left:5px solid {color};padding:20px;margin:24px 0;">
                <p style="margin:0;color:#374151;">Nuevo estado:</p>
                <strong style="font-size:1.4rem;color:{color};">{estado_texto}</strong>
              </div>

              {f'''<div style="background:#fef3c7;padding:15px;border-radius:8px;margin-bottom:24px;">
                <p style="margin:0;color:#92400e;font-weight:600;">Comentario del administrador:</p>
                <p style="margin:5px 0 0;color:#78350f;">{comentario}</p>
              </div>''' if comentario else ''}

              <p style="color:#374151;">Puedes consultar más detalles ingresando a la plataforma.</p>
              <div style="text-align:center;margin-top:30px;">
                <a href="http://localhost:5500/pages/login.html" 
                   style="background:#1a3a6b;color:white;padding:12px 25px;text-decoration:none;border-radius:6px;font-weight:600;">
                   Ir a la Plataforma
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
        print(f"[email_service] Error al enviar notificación a {email}: {e}")
        return False
