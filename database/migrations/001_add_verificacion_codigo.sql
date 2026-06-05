-- Migración 001: agregar columnas de verificación de código al login en dos pasos
-- Ejecutar UNA sola vez contra la base de datos Neon antes de desplegar en Vercel

ALTER TABLE usuarios
    ADD COLUMN IF NOT EXISTS verificacion_codigo  VARCHAR(10),
    ADD COLUMN IF NOT EXISTS verificacion_expira  TIMESTAMP;
