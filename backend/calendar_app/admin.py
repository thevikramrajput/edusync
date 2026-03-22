"""
EduSync — Calendar Admin.
"""
from django.contrib import admin
from .models import CalendarEntry


@admin.register(CalendarEntry)
class CalendarEntryAdmin(admin.ModelAdmin):
    list_display = ["title", "entry_type", "branch", "start_date"]
    list_filter = ["entry_type", "branch"]
    date_hierarchy = "start_date"
