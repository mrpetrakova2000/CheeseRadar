#!/bin/bash
set -e

echo "=== Airflow Startup ==="
echo "Using POSTGRES variables from Railway..."

echo "POSTGRES_HOST: ${POSTGRES_HOST:-NOT SET}"
echo "POSTGRES_PORT: ${POSTGRES_PORT:-NOT SET}"
echo "POSTGRES_DB: ${POSTGRES_DB:-NOT SET}"
echo "POSTGRES_USER: ${POSTGRES_USER:-NOT SET}"
echo "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:0:3}***"

export AIRFLOW__CORE__SQL_ALCHEMY_CONN="postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
echo "Airflow DB: postgresql+psycopg2://${POSTGRES_USER}:****@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"

echo "Waiting for PostgreSQL..."
sleep 10

if ! timeout 120 psql "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}" -c "SELECT 1;" > /dev/null 2>&1; then
    echo "WARNING: Cannot connect to PostgreSQL, but continuing..."
fi

sleep 150
echo "Initializing Airflow database..."
airflow db init

echo "Creating admin user..."
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin123

echo "Starting services..."
airflow scheduler &
exec airflow webserver --port 8080