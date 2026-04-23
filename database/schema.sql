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
DROP TABLE IF EXISTS programas_academicos;
DROP TABLE IF EXISTS universidades;

-- ============================================================
-- Tabla de Muestra programas_academicos
-- Almacena los programas academicos
-- ============================================================
CREATE TABLE programas_academicos (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL UNIQUE
);

-- ============================================================
-- Tabla de Muestra universidades
-- Almacena las universidades
-- ============================================================
CREATE TABLE universidades (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(200) NOT NULL,
    pais            VARCHAR(100) NOT NULL
);
-- ============================================================
-- Tabla tipos_documentos
-- Almacena los tipos de documentos de los usuarios
-- ============================================================
CREATE TABLE tipos_documentos (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(50) NOT NULL UNIQUE
);

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
    programa_id     INT REFERENCES programas_academicos(id),
    fecha_registro  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



-- ============================================================
-- TABLA 2: CONVOCATORIAS
-- Las oportunidades de intercambio disponibles
-- ============================================================
CREATE TABLE convocatorias (
    id               SERIAL PRIMARY KEY,
    titulo           VARCHAR(200) NOT NULL,
    universidad_id   INT REFERENCES universidades(id),
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
    tipo_documento_id INT REFERENCES tipos_documentos(id),
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

-- ============================================================
-- ÍNDICES
-- Aceleran las búsquedas más frecuentes de la aplicación
-- ============================================================

-- Buscar usuario por email (login)
CREATE INDEX idx_usuarios_email ON usuarios(email);

-- Buscar postulaciones de un estudiante específico
CREATE INDEX idx_postulaciones_estudiante ON postulaciones(estudiante_id);

-- Buscar postulaciones de una convocatoria específica
CREATE INDEX idx_postulaciones_convocatoria ON postulaciones(convocatoria_id);

-- Filtrar postulaciones por estado (en_revision / aprobada / rechazada)
CREATE INDEX idx_postulaciones_estado ON postulaciones(estado);

-- Buscar convocatorias por estado (activa / cerrada / proximamente)
CREATE INDEX idx_convocatorias_estado ON convocatorias(estado);

-- Buscar notificaciones no leídas de un usuario
CREATE INDEX idx_notificaciones_usuario ON notificaciones(usuario_id, leida);

-- ============================================================
-- TRIGGER
-- Actualiza automáticamente fecha_actualizacion en postulaciones
-- cada vez que el administrador cambia el estado o agrega comentario
-- ============================================================

CREATE OR REPLACE FUNCTION fn_actualizar_fecha_postulacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_actualizar_fecha_postulacion
BEFORE UPDATE ON postulaciones
FOR EACH ROW
EXECUTE FUNCTION fn_actualizar_fecha_postulacion();
