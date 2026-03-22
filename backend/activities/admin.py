"""
EduSync — Activities Admin.
"""
from django.contrib import admin
from .models import (
    Club, StudentClubMapping, Event,
    ActivityCategory, Activity, ActivityParticipation,
)


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "branch"]
    list_filter = ["category"]


@admin.register(StudentClubMapping)
class StudentClubMappingAdmin(admin.ModelAdmin):
    list_display = ["student", "club"]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "event_type", "scope", "start_date", "branch"]
    list_filter = ["event_type", "scope"]
    date_hierarchy = "start_date"


@admin.register(ActivityCategory)
class ActivityCategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ["name", "activity_type", "category", "date"]
    list_filter = ["activity_type", "category"]


@admin.register(ActivityParticipation)
class ActivityParticipationAdmin(admin.ModelAdmin):
    list_display = ["student", "activity", "position"]
    list_filter = ["position"]
