-- Migración 003: Nuevos estados de postulación y tipos de documentos de viaje

-- 1. Ampliar CHECK constraint para incluir docs_pendientes y completada
ALTER TABLE postulaciones DROP CONSTRAINT IF EXISTS postulaciones_estado_check;
ALTER TABLE postulaciones ADD CONSTRAINT postulaciones_estado_check
  CHECK (estado IN (
    'en_revision',
    'revisando_documentos',
    'necesita_correcciones',
    'aprobada',
    'rechazada',
    'docs_pendientes',
    'completada'
  ));

-- 2. Insertar tipos de documentos de viaje
INSERT INTO tipos_documentos (nombre) VALUES
  ('Pasaporte'),
  ('Seguro médico internacional'),
  ('Visa de estudiante'),
  ('Carta de aceptación universitaria')
ON CONFLICT (nombre) DO NOTHING;
