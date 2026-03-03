#!/bin/bash
set -e

echo "========================================="
echo "  EduSync — Container Startup"
echo "========================================="
echo "  DB Host:     db"
echo "  DB User:     ${POSTGRES_USER}"
echo "  DB Name:     ${POSTGRES_DB}"
echo "========================================="

if [ -n "${POSTGRES_PASSWORD}" ] && [ -n "${POSTGRES_USER}" ]; then
    echo ""
    echo "⏳ Waiting for PostgreSQL to accept connections..."
    DB_HOST=${DB_HOST:-db}
    until PGPASSWORD="${POSTGRES_PASSWORD}" psql \
      -h "${DB_HOST}" \
      -U "${POSTGRES_USER}" \
      -d "${POSTGRES_DB}" \
      -c '\q' > /dev/null 2>&1; do
      echo "  DB not ready — retrying in 2s..."
      sleep 2
    done
    echo "✅ PostgreSQL is ready!"
fi

echo ""
echo "🔄 Running migrations..."
python manage.py migrate --noinput

echo ""
echo "🌱 Seeding initial data..."
python manage.py seed_initial_data || true

echo ""
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput 2>/dev/null || true

# Railway provides PORT dynamically. Default to 8000 for local Compose.
export PORT="${PORT:-8000}"

echo ""
if [ "$#" -gt 0 ]; then
    # Run user CMD if provided (e.g., from docker-compose overrides or Railway startCommand)
    exec "$@"
else
    # Default fallback
    echo "🚀 Starting Gunicorn on 0.0.0.0:${PORT}..."
    exec gunicorn edusync.wsgi:application \
        --bind "0.0.0.0:${PORT}" \
        --workers 3 \
        --timeout 120 \
        --access-logfile - \
        --error-logfile -
fi
