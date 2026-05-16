
SELECT id, nombre, apellido, email, contrasena, rol
FROM usuarios
WHERE email = 'email_del_usuario';

-- [2] REGISTRO: Insertar nuevo estudiante
INSERT INTO usuarios (nombre, apellido, email, contrasena, rol, codigo, programa)
VALUES ('nombre', 'apellido', 'email', 'contrasena_encriptada', 'estudiante', 'codigo', 'programa');

-- [3] VER PERFIL: Obtener datos completos de un usuario por ID
SELECT id, nombre, apellido, email, rol, codigo, programa, fecha_registro
FROM usuarios
WHERE id = 1;

-- [4] LISTAR ADMINISTRADORES (para control interno)
SELECT id, nombre, apellido, email
FROM usuarios
WHERE rol = 'administrador';



SELECT id, titulo, universidad, pais, descripcion, requisitos,
       fecha_inicio, fecha_cierre, cupos, estado
FROM convocatorias
WHERE estado = 'activa'
ORDER BY fecha_cierre ASC;


SELECT id, titulo, universidad, pais, descripcion, requisitos,
       fecha_inicio, fecha_cierre, cupos, estado
FROM convocatorias
ORDER BY fecha_creacion DESC;


SELECT id, titulo, universidad, pais, descripcion, requisitos,
       fecha_inicio, fecha_cierre, cupos, estado
FROM convocatorias
WHERE id = 1;


INSERT INTO convocatorias (titulo, universidad, pais, descripcion, requisitos,
                           fecha_inicio, fecha_cierre, cupos, estado, creado_por)
VALUES ('título', 'universidad', 'país', 'descripción', 'requisitos',
        '2026-07-01', '2026-05-15', 5, 'activa', 1);


UPDATE convocatorias
SET estado = 'cerrada'
WHERE id = 1;




INSERT INTO postulaciones (estudiante_id, convocatoria_id)
VALUES (3, 1);


SELECT p.id,
       p.estado,
       p.comentario_admin,
       p.fecha_postulacion,
       p.fecha_actualizacion,
       c.titulo       AS convocatoria,
       c.universidad,
       c.pais
FROM postulaciones p
JOIN convocatorias c ON c.id = p.convocatoria_id
WHERE p.estudiante_id = 3
ORDER BY p.fecha_postulacion DESC;


SELECT p.id,
       u.nombre || ' ' || u.apellido  AS estudiante,
       u.email,
       u.programa,
       c.titulo                        AS convocatoria,
       c.universidad,
       c.pais,
       p.estado,
       p.comentario_admin,
       p.fecha_postulacion,
       p.fecha_actualizacion
FROM postulaciones p
JOIN usuarios      u ON u.id = p.estudiante_id
JOIN convocatorias c ON c.id = p.convocatoria_id
ORDER BY p.fecha_postulacion DESC;


SELECT p.id,
       u.nombre || ' ' || u.apellido AS estudiante,
       u.programa,
       c.titulo AS convocatoria,
       p.estado,
       p.fecha_postulacion
FROM postulaciones p
JOIN usuarios      u ON u.id = p.estudiante_id
JOIN convocatorias c ON c.id = p.convocatoria_id
WHERE p.estado = 'en_revision'   -- cambiar por: 'aprobada' | 'rechazada'
ORDER BY p.fecha_postulacion ASC;


UPDATE postulaciones
SET estado           = 'aprobada',    -- o 'rechazada'
    comentario_admin = 'Mensaje para el estudiante'
WHERE id = 3;


SELECT COUNT(*) AS ya_postulado
FROM postulaciones
WHERE estudiante_id   = 3
  AND convocatoria_id = 1;


SELECT
    COUNT(*)                                        AS total,
    COUNT(*) FILTER (WHERE estado = 'en_revision')  AS en_revision,
    COUNT(*) FILTER (WHERE estado = 'aprobada')     AS aprobadas,
    COUNT(*) FILTER (WHERE estado = 'rechazada')    AS rechazadas
FROM postulaciones;





INSERT INTO documentos (postulacion_id, nombre_archivo, tipo_documento, ruta_archivo)
VALUES (3, 'certificado_notas.pdf', 'Certificado de notas', 'uploads/postulacion_3/certificado_notas.pdf');


SELECT id, nombre_archivo, tipo_documento, ruta_archivo, fecha_subida
FROM documentos
WHERE postulacion_id = 3;





INSERT INTO notificaciones (usuario_id, mensaje)
VALUES (3, 'Tu postulación fue aprobada. ¡Felicitaciones!');


SELECT id, mensaje, fecha
FROM notificaciones
WHERE usuario_id = 3
  AND leida = FALSE
ORDER BY fecha DESC;


UPDATE notificaciones
SET leida = TRUE
WHERE id = 4;

UPDATE notificaciones
SET leida = TRUE
WHERE usuario_id = 3;


SELECT COUNT(*) AS no_leidas
FROM notificaciones
WHERE usuario_id = 3
  AND leida = FALSE;
