from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os

from database import get_db
from models import Usuario, ProgramaAcademico
from schemas import LoginRequest, LoginResponse, RegistroRequest, VerificarCodigoRequest
from auth import verificar_contrasena, hashear_contrasena, generar_token
from email_service import generar_y_guardar_codigo, enviar_codigo, verificar_codigo
from routers import convocatorias, postulaciones, admin

os.makedirs("uploads", exist_ok=True)

app = FastAPI(
    title="API Intercambios Académicos",
    description="API REST para la gestión de intercambios académicos — Universidad Piloto de Colombia",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- LOGIN (paso 1) ----
@app.post("/api/auth/login", tags=["Autenticación"],
          summary="Paso 1: verificar credenciales y enviar código al correo")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Verifica email y contraseña. Si son correctos envía un código de 6 dígitos
    al correo del usuario. El token solo se entrega tras verificar el código.

    Credenciales de prueba:
    - Admin: admin@upc.edu.co / admin
    - Estudiante: juan.vanegas@upc.edu.co / 1234
    """
    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
    if not usuario or not verificar_contrasena(request.contrasena, usuario.contrasena):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

    codigo = generar_y_guardar_codigo(usuario.email)
    enviado = enviar_codigo(usuario.email, codigo, usuario.nombre)

    if not enviado:
        raise HTTPException(status_code=500, detail="No se pudo enviar el código al correo")

    return {"mensaje": "Código enviado a tu correo", "email": usuario.email}

# ---- VERIFICAR CÓDIGO (paso 2) ----
@app.post("/api/auth/verificar-codigo", response_model=LoginResponse, tags=["Autenticación"],
          summary="Paso 2: ingresar el código recibido por correo y obtener el token")
def verificar_codigo_login(request: VerificarCodigoRequest, db: Session = Depends(get_db)):
    """Valida el código de 6 dígitos. Si es correcto devuelve el JWT."""
    if not verificar_codigo(request.email, request.codigo):
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

# ---- REGISTRO ----
@app.post("/api/auth/registro", response_model=LoginResponse, tags=["Autenticación"],
          summary="Crear cuenta de estudiante")
def registro(request: RegistroRequest, db: Session = Depends(get_db)):
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
        programa_id=programa.id
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    token = generar_token(nuevo.email, nuevo.rol)
    return LoginResponse(token=token, nombre=nuevo.nombre, apellido=nuevo.apellido,
                         email=nuevo.email, rol=nuevo.rol)

# ---- ROUTERS ----
app.include_router(convocatorias.router)
app.include_router(postulaciones.router)
app.include_router(admin.router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
