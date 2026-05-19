-- Migración 002: Ampliar estados de postulación para incluir sub-estados de revisión
ALTER TABLE postulaciones DROP CONSTRAINT IF EXISTS postulaciones_estado_check;
ALTER TABLE postulaciones ADD CONSTRAINT postulaciones_estado_check
  CHECK (estado IN ('en_revision', 'revisando_documentos', 'necesita_correcciones', 'aprobada', 'rechazada'));
