<<<<<<< HEAD
# 🎓 Aplicación de Gestión de Intercambios Académicos

Plataforma web centralizada para la gestión de intercambios académicos desarrollada por estudiantes de la **Universidad Piloto de Colombia** - Programa de Desarrollo Web.

---

## 👥 Equipo de Desarrollo

| Nombre | Rol |
|---|---|
| Leonardo Arias | Frontend |
| Juan Sebastián Sanabria Leiton | Base de Datos (PostgreSQL) |
| Juan Andrés Vanegas Guzmán | Backend (Java) |
| Luis Felipe Herrera Quintero | Desarrollo General |

---

## 📋 Descripción

Sistema web que permite centralizar y optimizar la gestión de intercambios académicos, facilitando:

- Consulta de convocatorias disponibles
- Registro y postulación de estudiantes
- Seguimiento del estado de solicitudes (aprobado / en revisión / rechazado)
- Panel de administración para gestores institucionales
- Notificaciones de cambios en el proceso

---

## 🏗️ Arquitectura

El sistema se divide en tres capas:

- **Frontend** → HTML5, CSS3, JavaScript puro
- **Backend** → Java (lógica de negocio y API REST)
- **Base de Datos** → PostgreSQL (base de datos relacional)

---

## 📁 Estructura del Proyecto

```
intercambios-academicos/
│
├── frontend/
│   ├── pages/
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── registro.html
│   │   ├── postulacion.html
│   │   ├── seguimiento.html
│   │   └── admin/
│   │       └── panel.html
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   └── main.js
│   └── assets/
│
├── backend/
│   └── src/
│       └── main/
│           └── java/
│               └── com/intercambios/
│                   ├── controllers/
│                   ├── models/
│                   ├── services/
│                   ├── repositories/
│                   └── config/
│
├── database/
│   ├── schema.sql
│   └── seed.sql
│
├── docs/
│   ├── proyecto_intercambios.docx
│   └── presentacion.pptx
│
├── .gitignore
└── README.md
```

---

## 🚀 Cómo clonar y configurar el proyecto

### Requisitos previos
- [Git](https://git-scm.com/)
- [Java JDK 17+](https://adoptium.net/)
- [PostgreSQL 15+](https://www.postgresql.org/)
- [Visual Studio Code](https://code.visualstudio.com/)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/intercambios-academicos.git

# 2. Entrar a la carpeta
cd intercambios-academicos

# 3. Crear la base de datos
psql -U postgres -f database/schema.sql

# 4. (Opcional) Cargar datos de prueba
psql -U postgres -f database/seed.sql
```

---

## 📅 Cronograma

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

## 📄 Licencia

Proyecto académico — Universidad Piloto de Colombia, 2026.
=======
# Gestion-de-intercambios-academicos
>>>>>>> 2c6c576c4c0514eded071ce98cd3a56ed61c66c8
