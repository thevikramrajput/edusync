"""
EduSync — Accounts URL Configuration.
JWT auth + CurrentUser profile + Student CRUD.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)
from .views import current_user_view, StudentViewSet

router = DefaultRouter()
router.register(r"students", StudentViewSet, basename="students")

urlpatterns = [
    # Auth endpoints
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
    path("me/", current_user_view, name="current_user"),

    # Student CRUD (nested under /api/v1/auth/ for now — will move to top-level)
    path("", include(router.urls)),
]
