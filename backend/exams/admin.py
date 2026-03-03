"""
EduSync — Exams Admin.
"""
from django.contrib import admin
from .models import ExamType, Exam, ExamMark


@admin.register(ExamType)
class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]


class ExamMarkInline(admin.TabularInline):
    model = ExamMark
    extra = 0


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ["exam_type", "class_assigned", "branch", "academic_year", "start_date"]
    list_filter = ["exam_type", "branch", "academic_year"]
    inlines = [ExamMarkInline]


@admin.register(ExamMark)
class ExamMarkAdmin(admin.ModelAdmin):
    list_display = ["student", "exam", "subject", "marks_obtained", "max_marks"]
    list_filter = ["exam__exam_type", "exam__branch"]
