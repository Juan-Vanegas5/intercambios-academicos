-- ============================================================
--  Migración 003 — Sincronizar esquema completo con los modelos
--  Aplica todos los cambios pendientes sin borrar datos.
--  Ejecutar desde la EC2:
--    python3 aplicar_migracion.py
-- ============================================================

-- 1. Tabla usuarios: agregar columnas de verificación 2FA
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS verificacion_codigo VARCHAR(10);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS verificacion_expira TIMESTAMP;

-- 2. Tabla postulaciones: ampliar CHECK de estados
ALTER TABLE postulaciones DROP CONSTRAINT IF EXISTS postulaciones_estado_check;
ALTER TABLE postulaciones ADD CONSTRAINT postulaciones_estado_check
    CHECK (estado IN ('en_revision', 'aprobada', 'rechazada', 'revisando_documentos', 'necesita_correcciones'));

-- 3. Tabla documentos: reemplazar BYTEA por s3_key
ALTER TABLE documentos ADD COLUMN IF NOT EXISTS s3_key VARCHAR(500);
ALTER TABLE documentos DROP COLUMN IF EXISTS contenido_archivo;
ALTER TABLE documentos DROP COLUMN IF EXISTS tamano_bytes;

-- 4. Tabla notificaciones: agregar columnas tipo y url
ALTER TABLE notificaciones ADD COLUMN IF NOT EXISTS tipo VARCHAR(30) DEFAULT 'general';
ALTER TABLE notificaciones ADD COLUMN IF NOT EXISTS url VARCHAR(300);
