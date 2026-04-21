-- ============================================================
-- DATOS DE PRUEBA (SEED)
-- Aplicación de Gestión de Intercambios Académicos
-- Universidad Piloto de Colombia
--
-- IMPORTANTE: Las contraseñas aquí son texto plano solo para
-- pruebas locales. En producción el backend debe encriptarlas
-- con BCrypt antes de guardarlas.
--
-- Ejecutar DESPUÉS de schema.sql:
--   psql -U postgres -d intercambios_db -f database/seed.sql
-- ============================================================


-- ============================================================
-- USUARIOS
-- ============================================================

INSERT INTO usuarios (nombre, apellido, email, contrasena, rol, codigo, programa) VALUES
-- Administradores
('Carlos',   'Pérez',           'admin@upc.edu.co',           'admin',    'administrador', NULL,        NULL),
('Sandra',   'Romero',          'sandra.romero@upc.edu.co',   'admin123', 'administrador', NULL,        NULL),

-- Estudiantes (los mismos que aparecen en el panel de admin del frontend)
('María',    'López',           'estudiante@upc.edu.co',      '1234',     'estudiante', '201901001', 'Ingeniería de Sistemas'),
('Carlos',   'Ruiz',            'carlos.ruiz@upc.edu.co',     '1234',     'estudiante', '201901002', 'Ingeniería Civil'),
('Juan',     'Vanegas',         'juan.vanegas@upc.edu.co',    '1234',     'estudiante', '201901003', 'Ingeniería de Sistemas'),
('Sofía',    'Martínez',        'sofia.martinez@upc.edu.co',  '1234',     'estudiante', '201901004', 'Administración de Empresas'),
('Andrés',   'Gómez',           'andres.gomez@upc.edu.co',    '1234',     'estudiante', '201901005', 'Arquitectura'),
('Laura',    'Hernández',       'laura.hernandez@upc.edu.co', '1234',     'estudiante', '201901006', 'Derecho');


-- ============================================================
-- CONVOCATORIAS
-- (coinciden con los datos del frontend en main.js)
-- ============================================================

INSERT INTO convocatorias (titulo, universidad, pais, descripcion, requisitos, fecha_inicio, fecha_cierre, cupos, estado, creado_por) VALUES
(
    'Intercambio Universidad de Barcelona',
    'Universidad de Barcelona',
    'España',
    'Programa semestral para estudiantes de tecnología e ingeniería con enfoque en innovación digital.',
    'Promedio mínimo 3.5, inglés B2, paz y salvo académico.',
    '2026-07-01', '2026-05-15', 5, 'activa',
    (SELECT id FROM usuarios WHERE email = 'admin@upc.edu.co')
),
(
    'Pasantía Universidad Nacional de México (UNAM)',
    'Universidad Nacional Autónoma de México',
    'México',
    'Intercambio académico enfocado en desarrollo de software y ciencias de la computación.',
    'Promedio mínimo 3.8, haber cursado al menos 5 semestres.',
    '2026-08-01', '2026-06-01', 3, 'activa',
    (SELECT id FROM usuarios WHERE email = 'admin@upc.edu.co')
),
(
    'Convenio Universidad de São Paulo',
    'Universidade de São Paulo',
    'Brasil',
    'Programa de un año completo con enfoque en investigación y desarrollo tecnológico.',
    'Promedio mínimo 4.0, inglés o portugués B1.',
    '2027-01-01', '2026-09-30', 2, 'proximamente',
    (SELECT id FROM usuarios WHERE email = 'sandra.romero@upc.edu.co')
),
(
    'Intercambio Instituto Tecnológico de Monterrey',
    'Instituto Tecnológico de Monterrey',
    'México',
    'Semestre académico en uno de los campus del Tecnológico de Monterrey.',
    'Promedio mínimo 3.6, sin materias reprobadas.',
    '2026-02-01', '2025-12-01', 4, 'cerrada',
    (SELECT id FROM usuarios WHERE email = 'sandra.romero@upc.edu.co')
);


-- ============================================================
-- POSTULACIONES
-- (coinciden con el panel de administrador del frontend)
-- ============================================================

INSERT INTO postulaciones (estudiante_id, convocatoria_id, estado, comentario_admin, fecha_postulacion) VALUES
(
    (SELECT id FROM usuarios WHERE email = 'maria.lopez@upc.edu.co'     LIMIT 1),
    (SELECT id FROM convocatorias WHERE titulo ILIKE '%Barcelona%'      LIMIT 1),
    'aprobada', 'Todo en orden. Bienvenida al programa.',
    '2026-04-08'
),
(
    (SELECT id FROM usuarios WHERE email = 'carlos.ruiz@upc.edu.co'    LIMIT 1),
    (SELECT id FROM convocatorias WHERE titulo ILIKE '%UNAM%'           LIMIT 1),
    'en_revision', NULL,
    '2026-04-09'
),
(
    (SELECT id FROM usuarios WHERE email = 'juan.vanegas@upc.edu.co'   LIMIT 1),
    (SELECT id FROM convocatorias WHERE titulo ILIKE '%Barcelona%'      LIMIT 1),
    'en_revision', NULL,
    '2026-04-10'
),
(
    (SELECT id FROM usuarios WHERE email = 'sofia.martinez@upc.edu.co' LIMIT 1),
    (SELECT id FROM convocatorias WHERE titulo ILIKE '%UNAM%'           LIMIT 1),
    'rechazada', 'Promedio por debajo del mínimo requerido.',
    '2026-04-11'
),
(
    (SELECT id FROM usuarios WHERE email = 'andres.gomez@upc.edu.co'   LIMIT 1),
    (SELECT id FROM convocatorias WHERE titulo ILIKE '%Barcelona%'      LIMIT 1),
    'aprobada', 'Excelente perfil académico.',
    '2026-04-12'
),
(
    (SELECT id FROM usuarios WHERE email = 'laura.hernandez@upc.edu.co' LIMIT 1),
    (SELECT id FROM convocatorias WHERE titulo ILIKE '%UNAM%'            LIMIT 1),
    'en_revision', NULL,
    '2026-04-13'
);


-- ============================================================
-- DOCUMENTOS
-- Archivos adjuntos de las postulaciones
-- ============================================================

INSERT INTO documentos (postulacion_id, nombre_archivo, tipo_documento, ruta_archivo) VALUES
-- Documentos de María López (postulación 1 - aprobada)
(1, 'certificado_notas_maria.pdf',  'Certificado de notas',    'uploads/postulacion_1/certificado_notas_maria.pdf'),
(1, 'paz_salvo_maria.pdf',          'Paz y salvo académico',   'uploads/postulacion_1/paz_salvo_maria.pdf'),
(1, 'certificado_idioma_maria.pdf', 'Certificado de idioma',   'uploads/postulacion_1/certificado_idioma_maria.pdf'),

-- Documentos de Juan Vanegas (postulación 3 - en revisión)
(3, 'certificado_notas_juan.pdf',   'Certificado de notas',    'uploads/postulacion_3/certificado_notas_juan.pdf'),
(3, 'paz_salvo_juan.pdf',           'Paz y salvo académico',   'uploads/postulacion_3/paz_salvo_juan.pdf'),

-- Documentos de Andrés Gómez (postulación 5 - aprobada)
(5, 'certificado_notas_andres.pdf', 'Certificado de notas',    'uploads/postulacion_5/certificado_notas_andres.pdf'),
(5, 'paz_salvo_andres.pdf',         'Paz y salvo académico',   'uploads/postulacion_5/paz_salvo_andres.pdf'),
(5, 'idioma_andres.pdf',            'Certificado de idioma',   'uploads/postulacion_5/idioma_andres.pdf');


-- ============================================================
-- NOTIFICACIONES
-- Mensajes automáticos generados al cambiar el estado
-- ============================================================

INSERT INTO notificaciones (usuario_id, mensaje, leida) VALUES
(
    (SELECT id FROM usuarios WHERE email = 'maria.lopez@upc.edu.co' LIMIT 1),
    '¡Felicitaciones! Tu postulación a la Universidad de Barcelona fue APROBADA. Revisa tu correo institucional para los próximos pasos.',
    FALSE
),
(
    (SELECT id FROM usuarios WHERE email = 'sofia.martinez@upc.edu.co' LIMIT 1),
    'Tu postulación a la UNAM fue rechazada. Motivo: Promedio por debajo del mínimo requerido. Puedes aplicar a otras convocatorias disponibles.',
    FALSE
),
(
    (SELECT id FROM usuarios WHERE email = 'andres.gomez@upc.edu.co' LIMIT 1),
    '¡Felicitaciones! Tu postulación a la Universidad de Barcelona fue APROBADA. Excelente perfil académico.',
    TRUE
),
(
    (SELECT id FROM usuarios WHERE email = 'juan.vanegas@upc.edu.co' LIMIT 1),
    'Tu postulación a la Universidad de Barcelona está siendo revisada. Te notificaremos pronto con el resultado.',
    FALSE
);
