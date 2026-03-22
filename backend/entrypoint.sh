#!/bin/bash
# NOTE: Do NOT use "set -e" here — we want Gunicorn to start
# even if migrations or seeding fail.

echo "========================================="
echo "  EduSync — Container Startup"
echo "========================================="

# ─── Wait for DB only if POSTGRES_* vars are set (Docker Compose) ────
# On Railway, DATABASE_URL is used directly by Django/dj-database-url,
# so we skip the psql wait and let Django handle connection.
if [ -n "${POSTGRES_PASSWORD}" ] && [ -n "${POSTGRES_USER}" ] && [ -n "${POSTGRES_DB}" ]; then
    DB_HOST=${DB_HOST:-db}
    echo "  DB Host:     ${DB_HOST}"
    echo "  DB User:     ${POSTGRES_USER}"
    echo "  DB Name:     ${POSTGRES_DB}"
    echo ""
    echo "⏳ Waiting for PostgreSQL to accept connections..."
    until PGPASSWORD="${POSTGRES_PASSWORD}" psql \
      -h "${DB_HOST}" \
      -U "${POSTGRES_USER}" \
      -d "${POSTGRES_DB}" \
      -c '\q' > /dev/null 2>&1; do
      echo "  DB not ready — retrying in 2s..."
      sleep 2
    done
    echo "✅ PostgreSQL is ready!"
else
    echo "  ℹ️  Using DATABASE_URL (Railway mode) — skipping psql wait."
    sleep 3
fi

echo ""
echo "🔄 Running migrations..."
python manage.py migrate --noinput || echo "⚠️  Migrations failed (non-fatal, continuing...)"

echo ""
echo "🌱 Seeding initial data..."
python manage.py seed_initial_data || echo "⚠️  seed_initial_data failed (non-fatal)"
python manage.py seed_test_users || echo "⚠️  seed_test_users failed (non-fatal)"

echo ""
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput 2>/dev/null || echo "⚠️  collectstatic failed (non-fatal)"

# Railway provides PORT dynamically. Default to 8000 for local Compose.
export PORT="${PORT:-8000}"

echo ""
echo "🚀 Starting Gunicorn on 0.0.0.0:${PORT}..."
exec gunicorn edusync.wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
