"""
EduSync — Lesson Plans Admin.
"""
from django.contrib import admin
from .models import LessonPlanTemplate, DailyLessonPlan


@admin.register(LessonPlanTemplate)
class LessonPlanTemplateAdmin(admin.ModelAdmin):
    list_display = ["subject", "created_by", "academic_year"]
    list_filter = ["academic_year"]


@admin.register(DailyLessonPlan)
class DailyLessonPlanAdmin(admin.ModelAdmin):
    list_display = ["faculty", "template", "class_assigned", "section", "date", "status"]
    list_filter = ["status", "branch"]
    date_hierarchy = "date"
