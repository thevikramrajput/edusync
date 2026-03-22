"""
EduSync — Core URL Configuration.
"""
from django.urls import path
from .views import health_check, liveness

urlpatterns = [
    path("", health_check, name="health-check"),
    path("live/", liveness, name="liveness"),
]
