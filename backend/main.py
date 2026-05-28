import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from database import get_db
from models import Usuario, ProgramaAcademico
from schemas import (
    LoginRequest, LoginResponse, RegistroRequest, VerificarCodigoRequest,
    ConfirmarRegistroRequest, ReenviarVerificacionRequest
)
from auth import verificar_contrasena, hashear_contrasena, generar_token
from email_service import (
    generar_y_guardar_codigo, enviar_codigo, verificar_codigo,
    generar_y_guardar_codigo_registro, enviar_codigo_registro
)
from routers import convocatorias, postulaciones, admin
from routers import notificaciones

_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()] or ["*"]

app = FastAPI(
    title="API Intercambios Académicos",
    description="API REST para la gestión de intercambios académicos — Universidad Piloto de Colombia",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── LOGIN paso 1: verificar credenciales → enviar código ──────────────────────

@app.post("/api/auth/login", tags=["Autenticación"],
          summary="Paso 1: verificar credenciales y enviar código al correo")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Verifica email y contraseña. Si son correctos envía un código de 6 dígitos
    al correo del usuario. El token solo se entrega tras verificar el código.
    """
    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
    if not usuario or not verificar_contrasena(request.contrasena, usuario.contrasena):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

    if not usuario.email_verificado:
        raise HTTPException(
            status_code=403,
            detail="Debes verificar tu correo antes de iniciar sesión. Revisa tu bandeja de entrada."
        )

    codigo = generar_y_guardar_codigo(usuario.email, db)
    enviado = enviar_codigo(usuario.email, codigo, usuario.nombre)

    if not enviado:
        raise HTTPException(status_code=500, detail="No se pudo enviar el código al correo")

    return {"mensaje": "Código enviado a tu correo", "email": usuario.email}


# ── LOGIN paso 2: verificar código → entregar JWT ─────────────────────────────

@app.post("/api/auth/verificar-codigo", response_model=LoginResponse, tags=["Autenticación"],
          summary="Paso 2: ingresar el código recibido por correo y obtener el token")
def verificar_codigo_login(request: VerificarCodigoRequest, db: Session = Depends(get_db)):
    """Valida el código de 6 dígitos. Si es correcto devuelve el JWT."""
    if not verificar_codigo(request.email, request.codigo, db):
        raise HTTPException(status_code=401, detail="Código incorrecto o expirado")

    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    token = generar_token(usuario.email, usuario.rol)
    return LoginResponse(
        token=token,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        rol=usuario.rol
    )


# ── REGISTRO paso 1: crear cuenta inactiva → enviar código de verificación ────

@app.post("/api/auth/registro", tags=["Autenticación"],
          summary="Paso 1 del registro: crear cuenta y enviar código de verificación al correo")
def registro(request: RegistroRequest, db: Session = Depends(get_db)):
    """
    Crea la cuenta con email_verificado=False y envía un código de 6 dígitos
    al correo del estudiante. La cuenta solo queda activa después de confirmar
    el código en /api/auth/confirmar-registro.
    """
    if db.query(Usuario).filter(Usuario.email == request.email).first():
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    programa = db.query(ProgramaAcademico).filter(ProgramaAcademico.nombre == request.programa).first()
    if not programa:
        programa = ProgramaAcademico(nombre=request.programa)
        db.add(programa)
        db.flush()

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
        email_verificado=False  # se activa en confirmar-registro
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    codigo = generar_y_guardar_codigo_registro(nuevo.email, db)
    enviado = enviar_codigo_registro(nuevo.email, codigo, nuevo.nombre)

    if not enviado:
        # Si SES falla, eliminamos el usuario para no dejar cuentas fantasma
        db.delete(nuevo)
        db.commit()
        raise HTTPException(status_code=500, detail="No se pudo enviar el código al correo. Intenta nuevamente.")

    return {"mensaje": "Código de verificación enviado a tu correo", "email": nuevo.email}


# ── REGISTRO paso 2: confirmar código → activar cuenta ────────────────────────

@app.post("/api/auth/confirmar-registro", response_model=LoginResponse, tags=["Autenticación"],
          summary="Paso 2 del registro: verificar código y activar la cuenta")
def confirmar_registro(request: ConfirmarRegistroRequest, db: Session = Depends(get_db)):
    """
    Valida el código de 6 dígitos enviado al correo durante el registro.
    Si es correcto, marca email_verificado=True y devuelve el JWT para
    iniciar sesión automáticamente.
    """
    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="No existe una cuenta con ese correo")

    if usuario.email_verificado:
        raise HTTPException(status_code=400, detail="Este correo ya fue verificado")

    if not verificar_codigo(request.email, request.codigo, db):
        raise HTTPException(status_code=401, detail="Código incorrecto o expirado")

    usuario.email_verificado = True
    db.commit()

    token = generar_token(usuario.email, usuario.rol)
    return LoginResponse(
        token=token,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        rol=usuario.rol
    )


# ── REENVIAR código de verificación de registro ──────────────────────────────

@app.post("/api/auth/reenviar-verificacion", tags=["Autenticación"],
          summary="Reenviar el código de verificación de registro")
def reenviar_verificacion(request: ReenviarVerificacionRequest, db: Session = Depends(get_db)):
    """
    Genera y reenvía un nuevo código al correo del usuario si aún no ha
    verificado su cuenta.
    """
    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="No existe una cuenta con ese correo")
    if usuario.email_verificado:
        raise HTTPException(status_code=400, detail="Este correo ya fue verificado")

    codigo  = generar_y_guardar_codigo_registro(usuario.email, db)
    enviado = enviar_codigo_registro(usuario.email, codigo, usuario.nombre)
    if not enviado:
        raise HTTPException(status_code=500, detail="No se pudo reenviar el código")

    return {"mensaje": "Código reenviado correctamente"}


# ── ROUTERS ───────────────────────────────────────────────────────────────────

app.include_router(convocatorias.router)
app.include_router(postulaciones.router)
app.include_router(admin.router)
app.include_router(notificaciones.router)
