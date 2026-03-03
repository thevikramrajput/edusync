#!/bin/bash
set -e

echo "========================================="
echo "  EduSync — Container Startup"
echo "========================================="
echo "  DB Host:     db"
echo "  DB User:     ${POSTGRES_USER}"
echo "  DB Name:     ${POSTGRES_DB}"
echo "========================================="

echo ""
echo "⏳ Waiting for PostgreSQL to accept connections..."

until PGPASSWORD="${POSTGRES_PASSWORD}" psql \
  -h db \
  -U "${POSTGRES_USER}" \
  -d "${POSTGRES_DB}" \
  -c '\q' > /dev/null 2>&1; do
  echo "  DB not ready — retrying in 2s..."
  sleep 2
done

echo "✅ PostgreSQL is ready!"
echo ""

echo "🔄 Running migrations..."
python manage.py migrate --noinput

echo ""
echo "🌱 Seeding initial data..."
python manage.py seed_initial_data

echo ""
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput 2>/dev/null || true

echo ""
echo "🚀 Starting Gunicorn on 0.0.0.0:8000..."
exec gunicorn edusync.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
