#!/bin/bash
# ============================================================
#  deploy.sh — Despliegue del backend en EC2 (Ubuntu)
#  Uso: bash deploy.sh
#  Requisitos: EC2 con Ubuntu 22.04, Python 3.11+, IAM Role con S3
# ============================================================

set -e  # Detener si cualquier comando falla

echo ""
echo "======================================================"
echo "  Despliegue — Intercambios Académicos (AWS EC2)"
echo "======================================================"

# ---------- 1. Actualizar paquetes del sistema ----------
echo ""
echo "[1/6] Actualizando paquetes del sistema..."
sudo apt-get update -q
sudo apt-get install -y python3.11 python3.11-venv python3-pip libpq-dev git --no-install-recommends

# ---------- 2. Crear entorno virtual ----------
echo ""
echo "[2/6] Preparando entorno virtual Python..."
cd ~/intercambios-academicos/backend

if [ ! -d "venv" ]; then
    python3.11 -m venv venv
    echo "  → Entorno virtual creado."
else
    echo "  → Entorno virtual ya existe, omitiendo creación."
fi

source venv/bin/activate

# ---------- 3. Instalar dependencias ----------
echo ""
echo "[3/6] Instalando dependencias Python..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "  → Dependencias instaladas."

# ---------- 4. Verificar .env ----------
echo ""
echo "[4/6] Verificando archivo .env..."
if [ ! -f ".env" ]; then
    echo "  ⚠  ADVERTENCIA: No se encontró el archivo .env"
    echo "     Copia backend/.env.example como backend/.env y rellena los valores."
    echo "     El servidor puede no funcionar correctamente sin este archivo."
else
    echo "  → .env encontrado."
fi

# ---------- 5. Migración de BD: agregar columna s3_key si no existe ----------
echo ""
echo "[5/6] Verificando esquema de base de datos..."
python3 - <<'PYEOF'
import os
from dotenv import load_dotenv
load_dotenv()
import sqlalchemy as sa

url = os.getenv("DATABASE_URL", "").replace("postgresql://", "postgresql+psycopg2://").replace("postgres://", "postgresql+psycopg2://")
engine = sa.create_engine(url)
with engine.connect() as conn:
    # Agregar s3_key si no existe (migración segura)
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='documentos' AND column_name='s3_key'
    """))
    if not result.fetchone():
        conn.execute(sa.text("ALTER TABLE documentos ADD COLUMN s3_key VARCHAR(500)"))
        conn.execute(sa.text("ALTER TABLE documentos DROP COLUMN IF EXISTS contenido_archivo"))
        conn.commit()
        print("  → Columna s3_key agregada y contenido_archivo eliminado de documentos.")
    else:
        print("  → Esquema ya está actualizado.")
PYEOF

# ---------- 6. Iniciar / reiniciar servidor ----------
echo ""
echo "[6/6] Iniciando servidor con uvicorn..."

# Detener instancia anterior si estaba corriendo
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 1

# Iniciar en segundo plano, guardando logs
nohup venv/bin/uvicorn main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --workers 2 \
    --log-level info \
    > ~/intercambios-backend.log 2>&1 &

sleep 2

# Verificar que levantó
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo ""
    echo "  ✓ Backend corriendo en http://0.0.0.0:8001"
    echo "  ✓ Logs en: ~/intercambios-backend.log"
    echo "  ✓ Docs API: http://$(curl -s ifconfig.me):8001/docs"
else
    echo ""
    echo "  ✗ ERROR: el servidor no pudo iniciar. Revisa los logs:"
    echo "    tail -50 ~/intercambios-backend.log"
    exit 1
fi

echo ""
echo "======================================================"
echo "  Despliegue completado exitosamente."
echo "======================================================"
