"""
EduSync — Assessments Admin Registration.
"""
from django.contrib import admin
from .models import (
    AssessmentType, AssessmentArea, AssessmentSubArea,
    AssessmentCriteria, StudentAssessment, StudentAssessmentScore,
)


@admin.register(AssessmentType)
class AssessmentTypeAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(AssessmentArea)
class AssessmentAreaAdmin(admin.ModelAdmin):
    list_display = ["name", "assessment_type", "order"]
    list_filter = ["assessment_type"]


@admin.register(AssessmentSubArea)
class AssessmentSubAreaAdmin(admin.ModelAdmin):
    list_display = ["name", "area", "order"]
    list_filter = ["area__assessment_type"]


@admin.register(AssessmentCriteria)
class AssessmentCriteriaAdmin(admin.ModelAdmin):
    list_display = ["description", "sub_area", "max_score", "order"]
    list_filter = ["sub_area__area__assessment_type"]


class ScoreInline(admin.TabularInline):
    model = StudentAssessmentScore
    extra = 0


@admin.register(StudentAssessment)
class StudentAssessmentAdmin(admin.ModelAdmin):
    list_display = ["student", "assessment_type", "quarter", "status", "branch"]
    list_filter = ["assessment_type", "status", "branch", "quarter"]
    inlines = [ScoreInline]


@admin.register(StudentAssessmentScore)
class StudentAssessmentScoreAdmin(admin.ModelAdmin):
    list_display = ["student_assessment", "criteria", "score"]
