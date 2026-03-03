"""
EduSync — Unified Calendar.
Aggregates events, activities, exams, and holidays into one view.
"""
import uuid
from django.db import models
from common.models import BaseModel


class CalendarEntry(BaseModel):
    """
    Unified calendar entry. Can link to an Event, Activity, Exam, or Holiday.
    """

    class EntryType(models.TextChoices):
        EVENT = "EVENT", "Event"
        ACTIVITY = "ACTIVITY", "Activity"
        EXAM = "EXAM", "Exam"
        HOLIDAY = "HOLIDAY", "Holiday"

    branch = models.ForeignKey(
        "core.Branch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="calendar_entries",
        help_text="NULL for entries visible to all branches.",
    )
    title = models.CharField(max_length=300)
    entry_type = models.CharField(
        max_length=10,
        choices=EntryType.choices,
    )
    related_entity_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="UUID of the linked Event/Activity/Exam.",
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "calendar entries"
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["start_date"]),
            models.Index(fields=["branch", "start_date"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.entry_type}) - {self.start_date}"
