# Sistema de Gestión de Intercambios Académicos

Plataforma web centralizada para la gestión de intercambios académicos desarrollada por estudiantes de la **Universidad Piloto de Colombia** — Programa de Desarrollo Web.

---

## Equipo de Desarrollo

| Nombre | Rol |
|---|---|
| Leonardo Arias | Frontend |
| Juan Sebastián Sanabria Leiton | Base de Datos (PostgreSQL) |
| Juan Andrés Vanegas Guzmán | Backend (Python / FastAPI) |
| Luis Felipe Herrera Quintero | Profesor |

---

## Descripción

Sistema web que permite centralizar y optimizar la gestión de intercambios académicos, facilitando:

- Consulta y filtrado de convocatorias disponibles
- Registro y autenticación de estudiantes con JWT
- Postulación a convocatorias con carga de documentos PDF
- Seguimiento del estado de solicitudes (en revisión / aprobada / rechazada)
- Panel de administración para gestores institucionales

---

## Arquitectura

El sistema se divide en tres capas:

- **Frontend** → HTML5, CSS3, JavaScript puro (sin frameworks)
- **Backend** → Python 3.12+ con FastAPI (API REST + JWT)
- **Base de Datos** → PostgreSQL en Neon Cloud

---

## Estructura del Proyecto

```
intercambios-academicos/
│
├── frontend/
│   ├── pages/
│   │   ├── index.html          ← Listado de convocatorias
│   │   ├── login.html          ← Inicio de sesión
│   │   ├── registro.html       ← Crear cuenta
│   │   ├── postulacion.html    ← Formulario de postulación
│   │   ├── seguimiento.html    ← Mis postulaciones
│   │   └── admin/
│   │       └── panel.html      ← Panel de administración
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── main.js             ← Utilidades compartidas
│
├── backend/
│   ├── main.py                 ← App FastAPI + login + registro
│   ├── models.py               ← Modelos SQLAlchemy
│   ├── schemas.py              ← Validación Pydantic
│   ├── auth.py                 ← JWT y guards de roles
│   ├── database.py             ← Conexión PostgreSQL
│   ├── requirements.txt
│   └── routers/
│       ├── convocatorias.py    ← GET /api/convocatorias
│       ├── postulaciones.py    ← POST/GET /api/postulaciones
│       └── admin.py            ← /api/admin/postulaciones
│
├── database/
│   ├── schema.sql              ← Crear tablas
│   └── seed.sql                ← Datos de prueba
│
└── docs/
    └── documentacion_completa.docx
```

---

## Endpoints de la API

| Método | Ruta | Acceso | Descripción |
|--------|------|--------|-------------|
| POST | `/api/auth/login` | Público | Iniciar sesión → devuelve JWT |
| POST | `/api/auth/registro` | Público | Crear cuenta de estudiante |
| GET | `/api/convocatorias` | Público | Convocatorias activas |
| GET | `/api/convocatorias/todas` | Público | Todas las convocatorias |
| GET | `/api/postulaciones/mis` | JWT | Mis postulaciones |
| POST | `/api/postulaciones` | JWT | Crear postulación |
| POST | `/api/postulaciones/{id}/documentos` | JWT | Subir documentos PDF |
| GET | `/api/admin/postulaciones` | Admin | Todas las postulaciones |
| PUT | `/api/admin/postulaciones/{id}/estado` | Admin | Aprobar / rechazar |

Documentación interactiva (Swagger): `http://localhost:8001/docs`

---

## Cómo ejecutar el proyecto

### Requisitos
- Python 3.12 o superior
- Cuenta en [Neon](https://neon.tech) con el esquema aplicado

### 1. Clonar el repositorio
```bash
git clone https://github.com/Juan-Vanegas5/intercambios-academicos.git
cd intercambios-academicos
```

### 2. Configurar el backend
Crear el archivo `backend/.env`:
```
DATABASE_URL=postgresql://usuario:password@host/database?sslmode=require
JWT_SECRET=intercambiosUPCsecretoJWT2026seguro
JWT_EXPIRATION_HOURS=24
```

### 3. Instalar dependencias e iniciar el servidor
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8001
```

### 4. Aplicar el esquema de base de datos (primera vez)
En el SQL Editor de [console.neon.tech](https://console.neon.tech):
1. Ejecutar `database/schema.sql`
2. Ejecutar `database/seed.sql`

### 5. Abrir el frontend
Abrir `frontend/pages/index.html` en el navegador.

---

## Credenciales de prueba

| Rol | Email | Contraseña |
|-----|-------|-----------|
| Administrador | admin@upc.edu.co | admin |
| Estudiante | juan.vanegas@upc.edu.co | 1234 |

---

## Cronograma

| Semana | Entrega | Responsable |
|---|---|---|
| 7 | Presentación inicial | Todo el equipo |
| 8 | Avance Frontend | Leonardo Arias |
| 9 | Esqueleto BD (PostgreSQL) | Juan Sanabria |
| 10 | Finalización Frontend | Leonardo Arias |
| 11 | Entrevista con expertos | Todo el equipo |
| 12 | Avance Backend | Juan Vanegas |
| 13 | Finalización BD | Juan Sanabria |
| 14 | Integración APIs con BD | Todo el equipo |
| 15 | Test y hosting | Todo el equipo |
| 16 | Conexión back, front y SQL | Todo el equipo |
| 17 | Test de estrés | Juan Vanegas |
| 18 | Entrega final | Todo el equipo |

---

## Licencia

Proyecto académico — Universidad Piloto de Colombia, 2026.
