"""
EduSync — Irregularities Admin.
"""
from django.contrib import admin
from .models import IrregularityType, StudentIrregularity


@admin.register(IrregularityType)
class IrregularityTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "applicable_role"]
    list_filter = ["applicable_role"]


@admin.register(StudentIrregularity)
class StudentIrregularityAdmin(admin.ModelAdmin):
    list_display = ["student", "irregularity_type", "date", "reported_by", "branch"]
    list_filter = ["irregularity_type", "branch", "quarter"]
    date_hierarchy = "date"
