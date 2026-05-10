from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os

from database import get_db
from models import Usuario, ProgramaAcademico
from schemas import LoginRequest, LoginResponse, RegistroRequest
from auth import verificar_contrasena, generar_token
from routers import convocatorias, postulaciones, admin

os.makedirs("uploads", exist_ok=True)

app = FastAPI(
    title="API Intercambios Académicos",
    description="API REST para la gestión de intercambios académicos — Universidad Piloto de Colombia",
    version="1.0.0"
)

# CORS: permite peticiones desde el frontend HTML
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- LOGIN ----
@app.post("/api/auth/login", response_model=LoginResponse, tags=["Autenticación"])
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Recibe **email** y **contraseña**, devuelve un token JWT.

    Usa el token en el candado 🔒 de Swagger para probar los demás endpoints.

    Credenciales de prueba:
    - Admin: admin@upc.edu.co / admin
    - Estudiante: juan.vanegas@upc.edu.co / 1234
    """
    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
    if not usuario or not verificar_contrasena(request.contrasena, usuario.contrasena):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

    token = generar_token(usuario.email, usuario.rol)
    return LoginResponse(
        token=token,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        rol=usuario.rol
    )

# ---- REGISTRO ----
@app.post("/api/auth/registro", response_model=LoginResponse, tags=["Autenticación"])
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
        contrasena=request.contrasena,
        rol="estudiante",
        codigo=request.codigo,
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
