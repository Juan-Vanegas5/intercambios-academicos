


-- Eliminar tablas si ya existen (para poder correr el script varias veces)
DROP TABLE IF EXISTS notificaciones CASCADE;
DROP TABLE IF EXISTS documentos CASCADE;
DROP TABLE IF EXISTS postulaciones CASCADE;
DROP TABLE IF EXISTS convocatorias CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;
DROP TABLE IF EXISTS tipos_documentos CASCADE;
DROP TABLE IF EXISTS programas_academicos CASCADE;
DROP TABLE IF EXISTS universidades CASCADE;


CREATE TABLE programas_academicos (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL UNIQUE
);


CREATE TABLE universidades (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(200) NOT NULL,
    pais            VARCHAR(100) NOT NULL
);

CREATE TABLE tipos_documentos (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(50) NOT NULL UNIQUE
);


CREATE TABLE usuarios (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    apellido        VARCHAR(100) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    contrasena      VARCHAR(255) NOT NULL,
    rol             VARCHAR(30)  NOT NULL CHECK (rol IN ('estudiante', 'administrador', 'universidad_destino')),
    universidad_id  INT REFERENCES universidades(id),
    codigo          VARCHAR(20),
    cedula          VARCHAR(20),
    celular         VARCHAR(20),
    programa_id     INT REFERENCES programas_academicos(id),
    totp_secret                VARCHAR(32),
    fecha_registro             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_verificado           BOOLEAN NOT NULL DEFAULT FALSE,
    token_verificacion_email   VARCHAR(64),
    token_verificacion_expira  TIMESTAMP
);




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


CREATE TABLE postulaciones (
    id                              SERIAL PRIMARY KEY,
    estudiante_id                   INT NOT NULL REFERENCES usuarios(id),
    convocatoria_id                 INT NOT NULL REFERENCES convocatorias(id),
    semestre                        INT,
    carta_intencion                 TEXT,
    estado                          VARCHAR(50) NOT NULL DEFAULT 'en_revision'
                                        CHECK (estado IN ('en_revision', 'aprobada', 'rechazada',
                                                          'revisando_documentos', 'necesita_correcciones',
                                                          'docs_pendientes', 'completada',
                                                          'docs_viaje_enviados', 'necesita_correcciones_viaje',
                                                          'pendiente_verificacion_uni',
                                                          'aprobada_universidad', 'rechazada_universidad',
                                                          'docs_extra_solicitados')),
    comentario_admin                TEXT,
    verificacion_universidad        VARCHAR(30) DEFAULT 'pendiente'
                                        CHECK (verificacion_universidad IN ('pendiente', 'aprobada', 'rechazada', 'docs_extra')),
    comentario_universidad          TEXT,
    fecha_verificacion_universidad  TIMESTAMP,
    fecha_postulacion               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (estudiante_id, convocatoria_id)
);


CREATE TABLE documentos (
    id               SERIAL PRIMARY KEY,
    postulacion_id   INT NOT NULL REFERENCES postulaciones(id),
    nombre_archivo   VARCHAR(255) NOT NULL,
    tipo_documento_id INT REFERENCES tipos_documentos(id),
    ruta_archivo     VARCHAR(500) NOT NULL,
    fecha_subida     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



CREATE TABLE notificaciones (
    id           SERIAL PRIMARY KEY,
    usuario_id   INT NOT NULL REFERENCES usuarios(id),
    mensaje      TEXT NOT NULL,
    leida        BOOLEAN DEFAULT FALSE,
    fecha        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



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
