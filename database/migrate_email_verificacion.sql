-- Migración: agregar columnas de verificación de email
-- Ejecutar UNA sola vez en la base de datos existente

ALTER TABLE usuarios
  ADD COLUMN IF NOT EXISTS email_verificado          BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS token_verificacion_email  VARCHAR(64),
  ADD COLUMN IF NOT EXISTS token_verificacion_expira TIMESTAMP;

-- Marcar como verificados todos los usuarios que ya tienen TOTP configurado
-- (ya completaron el flujo anterior y no deben quedar bloqueados)
UPDATE usuarios
SET email_verificado = TRUE
WHERE totp_secret IS NOT NULL;
