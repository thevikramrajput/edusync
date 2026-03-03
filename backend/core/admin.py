"""
EduSync — Core Admin Registration.
"""
from django.contrib import admin
from .models import School, Branch, AcademicYear, Quarter, GradeMapping


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "contact_email", "is_active"]
    search_fields = ["name", "code"]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["name", "full_name", "is_active", "created_at"]
    search_fields = ["name", "full_name"]
    list_filter = ["is_active"]


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ["year_label", "start_date", "end_date", "is_current", "is_active"]
    list_filter = ["is_current", "is_active"]


@admin.register(Quarter)
class QuarterAdmin(admin.ModelAdmin):
    list_display = ["name", "academic_year", "start_date", "end_date"]
    list_filter = ["academic_year"]


@admin.register(GradeMapping)
class GradeMappingAdmin(admin.ModelAdmin):
    list_display = ["grade", "min_percentage", "max_percentage"]
    ordering = ["-min_percentage"]
