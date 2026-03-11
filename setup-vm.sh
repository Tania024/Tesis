#!/bin/bash
# ============================================
# Setup Museo Pumapungo en VM Ubuntu
# Ejecutar como root o con sudo
# ============================================

set -e

echo "============================================"
echo " Museo Pumapungo - Instalacion en VM"
echo "============================================"

# ============================================
# 1. Instalar PostgreSQL (version disponible del sistema)
# ============================================
echo ""
echo "[1/5] Instalando PostgreSQL..."

if ! command -v psql &> /dev/null; then
    apt-get update
    apt-get install -y postgresql postgresql-client
    systemctl enable postgresql
    systemctl start postgresql
    PG_VER=$(psql --version | grep -oP '\d+' | head -1)
    echo "  PostgreSQL ${PG_VER} instalado."
else
    PG_VER=$(psql --version | grep -oP '\d+' | head -1)
    echo "  PostgreSQL ${PG_VER} ya esta instalado."
fi

# ============================================
# 2. Configurar BD y usuario
# ============================================
echo ""
echo "[2/5] Configurando base de datos..."

# Leer password del .env o usar default
DB_PASSWORD="${DB_PASSWORD:-CambiarEnProduccion2024}"
DB_USER="${DB_USER:-museo_app}"
DB_NAME="${DB_NAME:-museo_pumapungo}"

sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"
sudo -u postgres psql -d "${DB_NAME}" -c "GRANT ALL ON SCHEMA public TO ${DB_USER};"

echo "  BD '${DB_NAME}' con usuario '${DB_USER}' lista."

# ============================================
# 3. Cargar schema
# ============================================
echo ""
echo "[3/5] Cargando schema..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Verificar si las tablas ya existen
TABLES=$(PGPASSWORD="${DB_PASSWORD}" psql -h localhost -U "${DB_USER}" -d "${DB_NAME}" -tAc \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")

if [ "$TABLES" -lt 5 ]; then
    PGPASSWORD="${DB_PASSWORD}" psql -h localhost -U "${DB_USER}" -d "${DB_NAME}" \
        -f "${SCRIPT_DIR}/museo/museo_pumapungo.sql"
    echo "  Schema cargado correctamente."
else
    echo "  Schema ya existe (${TABLES} tablas). Saltando."
fi

# ============================================
# 4. Permitir conexiones desde Docker
# ============================================
echo ""
echo "[4/5] Configurando acceso PostgreSQL para Docker..."

PG_HBA=$(sudo -u postgres psql -tAc "SHOW hba_file")
PG_CONF=$(sudo -u postgres psql -tAc "SHOW config_file")

# Permitir conexiones desde red Docker (172.x.x.x)
if ! grep -q "172.0.0.0/8" "$PG_HBA" 2>/dev/null; then
    echo "# Docker containers" >> "$PG_HBA"
    echo "host    ${DB_NAME}    ${DB_USER}    172.0.0.0/8    md5" >> "$PG_HBA"
    echo "  Regla de acceso Docker agregada a pg_hba.conf"
fi

# Escuchar en todas las interfaces
if ! grep -q "listen_addresses = '\*'" "$PG_CONF" 2>/dev/null; then
    sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" "$PG_CONF"
    echo "  listen_addresses configurado a '*'"
fi

systemctl restart postgresql
echo "  PostgreSQL reiniciado."

# ============================================
# 5. Instalar Docker y cargar imagenes
# ============================================
echo ""
echo "[5/5] Configurando Docker..."

if ! command -v docker &> /dev/null; then
    echo "  Instalando Docker..."
    apt-get update
    apt-get install -y docker.io docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    echo "  Docker instalado."
else
    echo "  Docker ya esta instalado."
fi

# Cargar imagenes si existe el tar.gz
if [ -f "${SCRIPT_DIR}/museo-docker-images.tar.gz" ]; then
    echo "  Cargando imagenes Docker..."
    docker load < "${SCRIPT_DIR}/museo-docker-images.tar.gz"
    echo "  Imagenes cargadas."
else
    echo "  AVISO: No se encontro museo-docker-images.tar.gz"
    echo "  Debes cargarlo manualmente: docker load < museo-docker-images.tar.gz"
fi

# Crear .env si no existe
if [ ! -f "${SCRIPT_DIR}/.env" ]; then
    cp "${SCRIPT_DIR}/.env.example" "${SCRIPT_DIR}/.env"
    sed -i "s/CambiarEnProduccion2024/${DB_PASSWORD}/" "${SCRIPT_DIR}/.env"
    echo "  .env creado desde template."
fi

echo ""
echo "============================================"
echo " Instalacion completada!"
echo "============================================"
echo ""
echo " Para iniciar los servicios:"
echo "   cd ${SCRIPT_DIR}"
echo "   docker compose up -d"
echo ""
echo " Puertos:"
echo "   Frontend: http://localhost:3000"
echo "   API:      http://localhost:8000"
echo "   BD:       localhost:5432 (nativa)"
echo ""
echo " Para ver logs:"
echo "   docker compose logs -f"
echo ""
echo " IMPORTANTE: edita .env con tus API keys reales"
echo "============================================"
