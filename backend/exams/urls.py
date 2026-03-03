"""
EduSync — Exams URL Configuration.
ExamType, Exam, ExamMark (with bulk + report card).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExamTypeViewSet, ExamViewSet, ExamMarkViewSet

router = DefaultRouter()
router.register(r"types", ExamTypeViewSet, basename="exam-types")
router.register(r"list", ExamViewSet, basename="exams")
router.register(r"marks", ExamMarkViewSet, basename="exam-marks")

urlpatterns = [
    path("", include(router.urls)),
]
