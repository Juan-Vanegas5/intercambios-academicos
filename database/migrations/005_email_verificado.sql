-- Migración 005: Agregar columna email_verificado a usuarios
-- Permite el flujo MFA en registro: el usuario se crea con email_verificado=false
-- y solo se activa cuando ingresa el código de 6 dígitos recibido por correo.

ALTER TABLE usuarios
  ADD COLUMN IF NOT EXISTS email_verificado BOOLEAN NOT NULL DEFAULT false;

-- Los usuarios ya existentes se marcan como verificados (fueron creados antes del MFA)
UPDATE usuarios SET email_verificado = true WHERE email_verificado = false;
