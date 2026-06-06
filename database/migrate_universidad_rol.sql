-- Migración: agregar columnas del rol universidad_destino
-- Ejecutar en la BD de producción si aún no se han aplicado

-- 1. Columnas nuevas en postulaciones
ALTER TABLE postulaciones
  ADD COLUMN IF NOT EXISTS verificacion_universidad VARCHAR(30) DEFAULT 'pendiente',
  ADD COLUMN IF NOT EXISTS comentario_universidad TEXT,
  ADD COLUMN IF NOT EXISTS fecha_verificacion_universidad TIMESTAMP;

-- 2. Actualizar el CHECK de estado para incluir los nuevos valores
ALTER TABLE postulaciones DROP CONSTRAINT IF EXISTS postulaciones_estado_check;
ALTER TABLE postulaciones ADD CONSTRAINT postulaciones_estado_check
  CHECK (estado IN (
    'en_revision', 'aprobada', 'rechazada',
    'revisando_documentos', 'necesita_correcciones',
    'docs_pendientes', 'completada',
    'docs_viaje_enviados', 'necesita_correcciones_viaje',
    'pendiente_verificacion_uni',
    'aprobada_universidad', 'rechazada_universidad',
    'docs_extra_solicitados',
    'en_seguimiento', 'seguimiento_docs_enviados', 'seguimiento_completado'
  ));

-- 3. Agregar CHECK en verificacion_universidad si no existe
ALTER TABLE postulaciones DROP CONSTRAINT IF EXISTS postulaciones_verificacion_universidad_check;
ALTER TABLE postulaciones ADD CONSTRAINT postulaciones_verificacion_universidad_check
  CHECK (verificacion_universidad IN ('pendiente', 'aprobada', 'rechazada', 'docs_extra'));
