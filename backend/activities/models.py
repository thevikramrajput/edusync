"""
EduSync — Activities & Clubs.
Clubs (Yoga/Sports + All Club), Events, Activities, Participation.
"""
from django.db import models
from django.core.exceptions import ValidationError
from common.models import BaseModel, BranchScopedModel


# ─── Clubs ───────────────────────────────────────────────────

class Club(BaseModel):
    """
    School club. Each student must be in exactly 1 YOGA_SPORTS and 1 ALL_CLUB.
    """

    class Category(models.TextChoices):
        YOGA_SPORTS = "YOGA_SPORTS", "Yoga & Sports"
        ALL_CLUB = "ALL_CLUB", "All Club (Literary, Science, etc.)"

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=15, choices=Category.choices)
    branch = models.ForeignKey(
        "core.Branch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clubs",
        help_text="NULL if club is global (inter-branch).",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "category"],
                condition=models.Q(is_deleted=False),
                name="unique_active_club",
            ),
        ]
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class StudentClubMapping(BaseModel):
    """
    Maps a student to a club. Backend validation ensures:
    - Exactly 1 YOGA_SPORTS club
    - Exactly 1 ALL_CLUB
    """
    student = models.ForeignKey(
        "accounts.Student",
        on_delete=models.CASCADE,
        related_name="club_mappings",
    )
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name="student_mappings",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "club"],
                condition=models.Q(is_deleted=False),
                name="unique_active_student_club",
            ),
        ]

    def clean(self):
        """Enforce one club per category per student."""
        if not self.club_id:
            return
        existing = StudentClubMapping.objects.filter(
            student=self.student,
            club__category=self.club.category,
        ).exclude(pk=self.pk)
        if existing.exists():
            raise ValidationError(
                f"Student already has a {self.club.get_category_display()} club."
            )

    def __str__(self):
        return f"{self.student} → {self.club}"


# ─── Events ──────────────────────────────────────────────────

class Event(BaseModel):
    """
    Institutional events — annual function, celebrations, etc.
    """

    class EventType(models.TextChoices):
        ANNUAL_FUNCTION = "ANNUAL_FUNCTION", "Annual Function"
        CELEBRATION = "CELEBRATION", "Celebration"
        COMPETITION = "COMPETITION", "Competition"
        OTHER = "OTHER", "Other"

    class Scope(models.TextChoices):
        BRANCH = "BRANCH", "Branch"
        INTER_BRANCH = "INTER_BRANCH", "Inter-Branch"

    branch = models.ForeignKey(
        "core.Branch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events",
        help_text="NULL for inter-branch events.",
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default="")
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        default=EventType.OTHER,
    )
    scope = models.CharField(
        max_length=15,
        choices=Scope.choices,
        default=Scope.BRANCH,
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.title} ({self.start_date})"


# ─── Activities ──────────────────────────────────────────────

class ActivityCategory(BaseModel):
    """
    Category for competitive/performance activities.
    e.g. Assembly, School Function, Inter House, Inter Branch, Inter School.
    """
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "activity categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Activity(BaseModel):
    """
    Specific activity instance.
    """

    class ActivityType(models.TextChoices):
        INTER_BRANCH = "INTER_BRANCH", "Inter-Branch"
        INTER_HOUSE = "INTER_HOUSE", "Inter-House"
        INTER_SCHOOL = "INTER_SCHOOL", "Inter-School"
        CLUB = "CLUB", "Club Activity"

    category = models.ForeignKey(
        ActivityCategory,
        on_delete=models.PROTECT,
        related_name="activities",
    )
    name = models.CharField(max_length=300)
    activity_type = models.CharField(
        max_length=15,
        choices=ActivityType.choices,
    )
    branch_scope = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Which branches are involved.",
    )
    date = models.DateField()
    organized_by = models.ForeignKey(
        "accounts.Faculty",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="organized_activities",
    )

    class Meta:
        verbose_name_plural = "activities"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.name} ({self.date})"


class ActivityParticipation(BaseModel):
    """
    Student participation in an activity.
    """

    class Position(models.TextChoices):
        WINNER = "WINNER", "Winner"
        RUNNER_UP = "RUNNER_UP", "Runner Up"
        PARTICIPANT = "PARTICIPANT", "Participant"

    student = models.ForeignKey(
        "accounts.Student",
        on_delete=models.CASCADE,
        related_name="activity_participations",
    )
    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="participations",
    )
    position = models.CharField(
        max_length=15,
        choices=Position.choices,
        default=Position.PARTICIPANT,
    )
    remarks = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "activity"],
                condition=models.Q(is_deleted=False),
                name="unique_active_student_activity",
            ),
        ]

    def __str__(self):
        return f"{self.student} → {self.activity.name} ({self.position})"
