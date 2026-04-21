-- ============================================================
-- CONSULTAS SQL DE REFERENCIA
-- Aplicación de Gestión de Intercambios Académicos
-- Universidad Piloto de Colombia
--
-- Este archivo contiene todas las consultas que el backend
-- en Java necesitará para operar la aplicación.
-- Cada consulta está nombrada y explicada.
-- ============================================================


-- ============================================================
-- MÓDULO: USUARIOS
-- ============================================================

-- [1] LOGIN: Buscar usuario por email para autenticación
--     El backend verifica la contraseña con BCrypt después de obtener el registro
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


-- ============================================================
-- MÓDULO: CONVOCATORIAS
-- ============================================================

-- [5] PÁGINA PRINCIPAL: Listar todas las convocatorias activas
SELECT id, titulo, universidad, pais, descripcion, requisitos,
       fecha_inicio, fecha_cierre, cupos, estado
FROM convocatorias
WHERE estado = 'activa'
ORDER BY fecha_cierre ASC;

-- [6] LISTAR TODAS LAS CONVOCATORIAS (para filtros del frontend)
SELECT id, titulo, universidad, pais, descripcion, requisitos,
       fecha_inicio, fecha_cierre, cupos, estado
FROM convocatorias
ORDER BY fecha_creacion DESC;

-- [7] VER DETALLE DE UNA CONVOCATORIA
SELECT id, titulo, universidad, pais, descripcion, requisitos,
       fecha_inicio, fecha_cierre, cupos, estado
FROM convocatorias
WHERE id = 1;

-- [8] ADMIN - CREAR NUEVA CONVOCATORIA
INSERT INTO convocatorias (titulo, universidad, pais, descripcion, requisitos,
                           fecha_inicio, fecha_cierre, cupos, estado, creado_por)
VALUES ('título', 'universidad', 'país', 'descripción', 'requisitos',
        '2026-07-01', '2026-05-15', 5, 'activa', 1);

-- [9] ADMIN - CAMBIAR ESTADO DE UNA CONVOCATORIA
UPDATE convocatorias
SET estado = 'cerrada'
WHERE id = 1;


-- ============================================================
-- MÓDULO: POSTULACIONES
-- ============================================================

-- [10] POSTULARSE: Registrar nueva postulación de un estudiante
INSERT INTO postulaciones (estudiante_id, convocatoria_id)
VALUES (3, 1);

-- [11] SEGUIMIENTO: Ver todas las postulaciones de un estudiante con detalle
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

-- [12] ADMIN - VER TODAS LAS POSTULACIONES con datos del estudiante y convocatoria
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

-- [13] ADMIN - FILTRAR POSTULACIONES POR ESTADO
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

-- [14] ADMIN - APROBAR O RECHAZAR UNA POSTULACIÓN
--      (el trigger actualiza fecha_actualizacion automáticamente)
UPDATE postulaciones
SET estado           = 'aprobada',    -- o 'rechazada'
    comentario_admin = 'Mensaje para el estudiante'
WHERE id = 3;

-- [15] VERIFICAR SI UN ESTUDIANTE YA APLICÓ A UNA CONVOCATORIA
--      (evita duplicados; la tabla ya tiene UNIQUE, pero útil para
--       mostrar un mensaje amigable antes de intentar insertar)
SELECT COUNT(*) AS ya_postulado
FROM postulaciones
WHERE estudiante_id   = 3
  AND convocatoria_id = 1;

-- [16] ESTADÍSTICAS DEL PANEL ADMIN
SELECT
    COUNT(*)                                        AS total,
    COUNT(*) FILTER (WHERE estado = 'en_revision')  AS en_revision,
    COUNT(*) FILTER (WHERE estado = 'aprobada')     AS aprobadas,
    COUNT(*) FILTER (WHERE estado = 'rechazada')    AS rechazadas
FROM postulaciones;


-- ============================================================
-- MÓDULO: DOCUMENTOS
-- ============================================================

-- [17] REGISTRAR DOCUMENTO AL POSTULARSE
INSERT INTO documentos (postulacion_id, nombre_archivo, tipo_documento, ruta_archivo)
VALUES (3, 'certificado_notas.pdf', 'Certificado de notas', 'uploads/postulacion_3/certificado_notas.pdf');

-- [18] VER DOCUMENTOS DE UNA POSTULACIÓN
SELECT id, nombre_archivo, tipo_documento, ruta_archivo, fecha_subida
FROM documentos
WHERE postulacion_id = 3;


-- ============================================================
-- MÓDULO: NOTIFICACIONES
-- ============================================================

-- [19] CREAR NOTIFICACIÓN para un usuario (se llama al aprobar/rechazar)
INSERT INTO notificaciones (usuario_id, mensaje)
VALUES (3, 'Tu postulación fue aprobada. ¡Felicitaciones!');

-- [20] VER NOTIFICACIONES NO LEÍDAS DE UN USUARIO
SELECT id, mensaje, fecha
FROM notificaciones
WHERE usuario_id = 3
  AND leida = FALSE
ORDER BY fecha DESC;

-- [21] MARCAR NOTIFICACIÓN COMO LEÍDA
UPDATE notificaciones
SET leida = TRUE
WHERE id = 4;

-- [22] MARCAR TODAS LAS NOTIFICACIONES DE UN USUARIO COMO LEÍDAS
UPDATE notificaciones
SET leida = TRUE
WHERE usuario_id = 3;

-- [23] CONTAR NOTIFICACIONES NO LEÍDAS (para el badge del menú)
SELECT COUNT(*) AS no_leidas
FROM notificaciones
WHERE usuario_id = 3
  AND leida = FALSE;
