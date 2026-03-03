"""
EduSync — URL Configuration.
All API endpoints live under /api/v1/ for versioning.
Swagger docs at /api/docs/.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),

    # ─── API Documentation ───────────────────────────────
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    # ─── Health Check ────────────────────────────────────
    path("api/v1/health/", include("core.urls")),

    # ─── API v1 — Phase 2A (Active) ─────────────────────
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/exams/", include("exams.urls")),

    # ─── API v1 — Phase 3 (Active) ──────────────────────
    path("api/v1/assessments/", include("assessments.urls")),

    # ─── Future Phases ───────────────────────────────────
    # path("api/v1/academics/", include("academics.urls")),
    # path("api/v1/irregularities/", include("irregularities.urls")),
    # path("api/v1/activities/", include("activities.urls")),
    # path("api/v1/calendar/", include("calendar_app.urls")),
    # path("api/v1/feedback/", include("feedback.urls")),
]
