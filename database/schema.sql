-- ============================================================
-- ESQUEMA DE BASE DE DATOS
-- Aplicación de Gestión de Intercambios Académicos
-- Universidad Piloto de Colombia
-- ============================================================

-- Eliminar tablas si ya existen (para poder correr el script varias veces)
DROP TABLE IF EXISTS notificaciones CASCADE;
DROP TABLE IF EXISTS documentos CASCADE;
DROP TABLE IF EXISTS postulaciones CASCADE;
DROP TABLE IF EXISTS convocatorias CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;

-- ============================================================
-- TABLA 1: USUARIOS
-- Almacena tanto estudiantes como administradores
-- ============================================================
CREATE TABLE usuarios (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    apellido        VARCHAR(100) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    contrasena      VARCHAR(255) NOT NULL,
    rol             VARCHAR(20)  NOT NULL CHECK (rol IN ('estudiante', 'administrador')),
    codigo          VARCHAR(20),
    programa        VARCHAR(100),
    fecha_registro  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLA 2: CONVOCATORIAS
-- Las oportunidades de intercambio disponibles
-- ============================================================
CREATE TABLE convocatorias (
    id               SERIAL PRIMARY KEY,
    titulo           VARCHAR(200) NOT NULL,
    universidad      VARCHAR(200) NOT NULL,
    pais             VARCHAR(100) NOT NULL,
    descripcion      TEXT,
    requisitos       TEXT,
    fecha_inicio     DATE NOT NULL,
    fecha_cierre     DATE NOT NULL,
    cupos            INT  NOT NULL DEFAULT 1,
    estado           VARCHAR(20) NOT NULL CHECK (estado IN ('activa', 'cerrada', 'proximamente')),
    creado_por       INT REFERENCES usuarios(id),
    fecha_creacion   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLA 3: POSTULACIONES
-- Registra qué estudiante aplicó a qué convocatoria
-- ============================================================
CREATE TABLE postulaciones (
    id                  SERIAL PRIMARY KEY,
    estudiante_id       INT NOT NULL REFERENCES usuarios(id),
    convocatoria_id     INT NOT NULL REFERENCES convocatorias(id),
    estado              VARCHAR(20) NOT NULL DEFAULT 'en_revision'
                            CHECK (estado IN ('en_revision', 'aprobada', 'rechazada')),
    comentario_admin    TEXT,
    fecha_postulacion   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (estudiante_id, convocatoria_id)
);

-- ============================================================
-- TABLA 4: DOCUMENTOS
-- Archivos que sube el estudiante al postularse
-- ============================================================
CREATE TABLE documentos (
    id               SERIAL PRIMARY KEY,
    postulacion_id   INT NOT NULL REFERENCES postulaciones(id),
    nombre_archivo   VARCHAR(255) NOT NULL,
    tipo_documento   VARCHAR(100) NOT NULL,
    ruta_archivo     VARCHAR(500) NOT NULL,
    fecha_subida     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLA 5: NOTIFICACIONES
-- Mensajes que recibe el usuario dentro de la plataforma
-- ============================================================
CREATE TABLE notificaciones (
    id           SERIAL PRIMARY KEY,
    usuario_id   INT NOT NULL REFERENCES usuarios(id),
    mensaje      TEXT NOT NULL,
    leida        BOOLEAN DEFAULT FALSE,
    fecha        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
