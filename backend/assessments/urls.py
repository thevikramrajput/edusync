"""
EduSync — Assessments URL Configuration.
AssessmentType (types/) and StudentAssessment (student/).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssessmentTypeViewSet, StudentAssessmentViewSet

router = DefaultRouter()
router.register(r"types", AssessmentTypeViewSet, basename="assessment-types")
router.register(r"student", StudentAssessmentViewSet, basename="student-assessments")

urlpatterns = [
    path("", include(router.urls)),
]
