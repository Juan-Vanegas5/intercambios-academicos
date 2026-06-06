from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
import secrets
import datetime
import pyotp
import qrcode
import base64
from io import BytesIO

from database import get_db
from models import Usuario, ProgramaAcademico
from schemas import (LoginRequest, LoginResponse, RegistroRequest,
                     TOTPSetupResponse, TOTPVerifyRequest, TOTPConfirmSetupRequest)
from auth import verificar_contrasena, hashear_contrasena, generar_token
from routers import convocatorias, postulaciones, admin, notificaciones, universidad
import email_service
from dotenv import load_dotenv

load_dotenv()

os.makedirs("uploads", exist_ok=True)

app = FastAPI(
    title="API Intercambios Académicos",
    description="API REST para la gestión de intercambios académicos — Universidad Piloto de Colombia",
    version="2.0.0"
)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR 500] {request.method} {request.url} → {exc}")
    origin = request.headers.get("origin", "")
    cors_headers = {}
    if origin:
        cors_headers["Access-Control-Allow-Origin"] = origin
        cors_headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
        headers=cors_headers,
    )


# ---- helpers TOTP ----
def generar_qr_base64(usuario: Usuario, secret: str) -> str:
    """Genera la imagen QR como string base64 para mostrar en el frontend."""
    uri = pyotp.TOTP(secret).provisioning_uri(
        name=usuario.email,
        issuer_name="Intercambios UPC"
    )
    img = qrcode.make(uri)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


# ---- LOGIN (paso 1): verificar credenciales ----
@app.post("/api/auth/login", tags=["Autenticación"],
          summary="Paso 1: verificar credenciales")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Verifica email y contraseña.
    - Si el usuario ya configuró TOTP → responde requiere_totp: true
    - Si no ha configurado TOTP → responde requiere_setup: true + QR

    Credenciales de prueba:
    - Admin: admin@upc.edu.co / admin
    - Estudiante: juan.vanegas@upc.edu.co / 1234
    """
    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
    if not usuario or not verificar_contrasena(request.contrasena, usuario.contrasena):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

    if not usuario.email_verificado:
        raise HTTPException(status_code=403, detail="Debes verificar tu correo electrónico antes de iniciar sesión. Revisa tu bandeja de entrada.")

    if usuario.totp_secret:
        # Ya tiene TOTP configurado → pedir código
        return {"requiere_totp": True, "requiere_setup": False, "email": usuario.email}
    else:
        # No tiene TOTP → generar secret y QR para configurar
        secret = pyotp.random_base32()
        qr_base64 = generar_qr_base64(usuario, secret)
        return {
            "requiere_totp": False,
            "requiere_setup": True,
            "email": usuario.email,
            "qr_code": qr_base64,
            "secret": secret
        }


# ---- TOTP SETUP: confirmar configuración con primer código ----
@app.post("/api/auth/totp/confirmar-setup", tags=["Autenticación"],
          summary="Confirmar configuración TOTP con el primer código")
def confirmar_setup_totp(request: TOTPConfirmSetupRequest, db: Session = Depends(get_db)):
    """El usuario escanea el QR, ingresa el primer código para confirmar y se guarda el secret."""
    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    totp = pyotp.TOTP(request.secret)
    if not totp.verify(request.codigo, valid_window=1):
        raise HTTPException(status_code=401, detail="Código incorrecto. Verifica que escaneaste el QR correctamente.")

    # Guardar el secret en la BD
    usuario.totp_secret = request.secret
    db.commit()

    # Generar token JWT
    token = generar_token(usuario.email, usuario.rol)
    return {
        "token": token,
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "email": usuario.email,
        "rol": usuario.rol
    }


# ---- VERIFICAR TOTP (paso 2 del login) ----
@app.post("/api/auth/totp/verificar", response_model=LoginResponse, tags=["Autenticación"],
          summary="Paso 2: verificar código TOTP de Google Authenticator")
def verificar_totp(request: TOTPVerifyRequest, db: Session = Depends(get_db)):
    """Valida el código de 6 dígitos de Google Authenticator."""
    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not usuario.totp_secret:
        raise HTTPException(status_code=400, detail="TOTP no configurado para este usuario")

    totp = pyotp.TOTP(usuario.totp_secret)
    if not totp.verify(request.codigo, valid_window=1):
        raise HTTPException(status_code=401, detail="Código incorrecto o expirado")

    token = generar_token(usuario.email, usuario.rol)
    return LoginResponse(
        token=token,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        rol=usuario.rol
    )


# ---- REGISTRO ----
@app.post("/api/auth/registro", tags=["Autenticación"],
          summary="Crear cuenta de estudiante")
def registro(request: RegistroRequest, db: Session = Depends(get_db)):
    ahora = datetime.datetime.now()
    existente = db.query(Usuario).filter(Usuario.email == request.email).first()
    if existente:
        if existente.email_verificado:
            raise HTTPException(status_code=400, detail="El correo ya está registrado")
        # Registro pendiente: si el token expiró, eliminar y permitir nuevo intento
        if existente.token_verificacion_expira and ahora > existente.token_verificacion_expira:
            db.delete(existente)
            db.commit()
        else:
            raise HTTPException(status_code=400, detail="Ya se envió un correo de verificación a esa dirección. Revisa tu bandeja de entrada o espera 5 minutos para intentar de nuevo.")

    programa = db.query(ProgramaAcademico).filter(ProgramaAcademico.nombre == request.programa).first()
    if not programa:
        programa = ProgramaAcademico(nombre=request.programa)
        db.add(programa)
        db.flush()

    token_verificacion = secrets.token_urlsafe(32)
    expira = ahora + datetime.timedelta(minutes=5)

    nuevo = Usuario(
        nombre=request.nombre,
        apellido=request.apellido,
        email=request.email,
        contrasena=hashear_contrasena(request.contrasena),
        rol="estudiante",
        codigo=request.codigo,
        cedula=request.cedula,
        celular=request.celular,
        programa_id=programa.id,
        email_verificado=False,
        token_verificacion_email=token_verificacion,
        token_verificacion_expira=expira
    )
    db.add(nuevo)
    db.commit()

    frontend_url = os.getenv("FRONTEND_URL", "https://intercambiosupc.lat")
    link = f"{frontend_url}/pages/verificar-email.html?token={token_verificacion}"
    email_service.enviar_verificacion_registro(request.email, request.nombre, link)

    return {
        "mensaje": "Te enviamos un enlace de verificación. Tienes 5 minutos para confirmar tu correo.",
        "email": request.email
    }


# ---- VERIFICAR EMAIL ----
@app.get("/api/auth/verificar-email", tags=["Autenticación"],
         summary="Verificar correo con el token del enlace enviado por email")
def verificar_email(token: str = Query(...), db: Session = Depends(get_db)):
    ahora = datetime.datetime.now()
    usuario = db.query(Usuario).filter(Usuario.token_verificacion_email == token).first()
    if not usuario:
        raise HTTPException(status_code=400, detail="El enlace no es válido o ya fue utilizado.")

    if ahora > usuario.token_verificacion_expira:
        db.delete(usuario)
        db.commit()
        raise HTTPException(status_code=400, detail="El enlace expiró. Tu registro fue anulado. Por favor regístrate de nuevo.")

    usuario.email_verificado = True
    usuario.token_verificacion_email = None
    usuario.token_verificacion_expira = None
    db.commit()

    secret = pyotp.random_base32()
    qr_base64 = generar_qr_base64(usuario, secret)

    return {
        "requiere_setup": True,
        "email": usuario.email,
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "qr_code": qr_base64,
        "secret": secret
    }


# ---- ROUTERS ----
app.include_router(convocatorias.router)
app.include_router(postulaciones.router)
app.include_router(admin.router)
app.include_router(notificaciones.router)
app.include_router(universidad.router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
