from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db
from models import Usuario
from schemas import LoginRequest, LoginResponse
from auth import verificar_contrasena, generar_token
from routers import convocatorias, postulaciones, admin

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

# ---- ROUTERS ----
app.include_router(convocatorias.router)
app.include_router(postulaciones.router)
app.include_router(admin.router)
