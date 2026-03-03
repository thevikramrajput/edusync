"""
EduSync — Lesson Plan System (V2 Ready).
Templates (HOD-created) + Daily Plans (Teacher-filled).
"""
from django.db import models
from django.conf import settings
from common.models import BaseModel, BranchScopedModel


class LessonPlanTemplate(BaseModel):
    """
    Lesson plan template created by HOD for a subject.
    Defines structure: tools, objectives, assessment methods.
    """
    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.CASCADE,
        related_name="lesson_templates",
    )
    created_by = models.ForeignKey(
        "accounts.Faculty",
        on_delete=models.PROTECT,
        related_name="created_templates",
        help_text="HOD who created this template.",
    )
    academic_year = models.ForeignKey(
        "core.AcademicYear",
        on_delete=models.PROTECT,
        related_name="lesson_templates",
    )
    tools_required = models.TextField(
        blank=True, default="",
        help_text="Tools/materials required for this subject.",
    )
    learning_objectives = models.TextField(
        blank=True, default="",
    )
    assessment_method = models.TextField(
        blank=True, default="",
    )
    resources = models.TextField(
        blank=True, default="",
    )
    homework_pattern = models.TextField(
        blank=True, default="",
    )

    class Meta:
        ordering = ["-academic_year__start_date", "subject__name"]

    def __str__(self):
        return f"Template: {self.subject} ({self.academic_year})"


class DailyLessonPlan(BranchScopedModel):
    """
    Daily lesson plan filled by a teacher based on an HOD's template.
    Status workflow: DRAFT → SUBMITTED → APPROVED.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"

    template = models.ForeignKey(
        LessonPlanTemplate,
        on_delete=models.PROTECT,
        related_name="daily_plans",
    )
    faculty = models.ForeignKey(
        "accounts.Faculty",
        on_delete=models.PROTECT,
        related_name="daily_lesson_plans",
    )
    class_assigned = models.ForeignKey(
        "academics.Class",
        on_delete=models.PROTECT,
        related_name="lesson_plans",
    )
    section = models.ForeignKey(
        "academics.Section",
        on_delete=models.PROTECT,
        related_name="lesson_plans",
    )
    date = models.DateField()
    topic_covered = models.TextField()
    homework_given = models.TextField(blank=True, default="")
    remarks = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    approved_by = models.ForeignKey(
        "accounts.Faculty",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_lesson_plans",
        help_text="HOD who approved this plan.",
    )

    class Meta:
        ordering = ["-date"]
        indexes = [
            models.Index(
                fields=["faculty", "date"],
                condition=models.Q(is_deleted=False),
                name="dlp_faculty_date_idx",
            ),
            models.Index(
                fields=["branch", "class_assigned", "date"],
                condition=models.Q(is_deleted=False),
                name="dlp_branch_cls_date_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.faculty} - {self.template.subject} "
            f"({self.class_assigned}-{self.section}) {self.date}"
        )
