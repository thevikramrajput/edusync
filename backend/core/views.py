"""
EduSync — Core Views: Health Check (Liveness + Readiness).
"""
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    GET /api/v1/health/
    Readiness probe: DB connectivity + migration status.
    Safe for load balancers and uptime monitors.
    """
    db_ok = False
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        pass

    migrations_ok = False
    try:
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        migrations_ok = len(plan) == 0
    except Exception:
        pass

    all_ok = db_ok and migrations_ok
    return Response({
        "status": "OK" if all_ok else "DEGRADED",
        "database": "connected" if db_ok else "unavailable",
        "migrations": "up_to_date" if migrations_ok else "pending",
    }, status=200 if all_ok else 503)


@api_view(["GET"])
@permission_classes([AllowAny])
def liveness(request):
    """
    GET /api/v1/health/live/
    Liveness probe: confirms the Django process is alive.
    Does NOT check external dependencies — only that the app responds.
    """
    return Response({"status": "alive"}, status=200)
