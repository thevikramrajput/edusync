"""
EduSync — Academics Admin Registration.
"""
from django.contrib import admin
from .models import Class, Section, Subject, House, FacultySubjectMapping


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ["name", "branch", "is_active"]
    list_filter = ["branch"]


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ["name", "class_ref", "is_active"]
    list_filter = ["class_ref__branch"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name", "branch", "is_active"]
    list_filter = ["branch"]


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ["name", "branch", "is_active"]
    list_filter = ["branch"]


@admin.register(FacultySubjectMapping)
class FacultySubjectMappingAdmin(admin.ModelAdmin):
    list_display = ["faculty", "subject", "class_assigned", "section"]
    list_filter = ["subject", "class_assigned"]
