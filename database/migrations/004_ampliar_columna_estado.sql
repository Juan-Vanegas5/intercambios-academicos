-- Migración 004: Ampliar columna estado de VARCHAR(20) a VARCHAR(50)
-- Necesario porque 'necesita_correcciones' tiene 22 caracteres

ALTER TABLE postulaciones ALTER COLUMN estado TYPE VARCHAR(50);
