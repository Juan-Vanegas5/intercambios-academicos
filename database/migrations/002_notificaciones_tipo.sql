-- Migración 002: agregar columnas 'tipo' y 'url' a notificaciones
-- para soportar notificaciones clickeables con redirección
 
ALTER TABLE notificaciones
    ADD COLUMN IF NOT EXISTS tipo     VARCHAR(30) DEFAULT 'general',
    ADD COLUMN IF NOT EXISTS url      VARCHAR(300);
 