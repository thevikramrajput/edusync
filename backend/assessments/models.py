"""
EduSync — Flexible Assessment Engine.
Handles Social, Physical, Co-Curricular, and MIA assessments.
Structure: Type → Area → SubArea → Criteria → StudentAssessment → Scores.
"""
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from common.models import BaseModel, BranchScopedModel


class AssessmentType(BaseModel):
    """
    Top-level assessment category.
    e.g. SOCIAL_EMOTIONAL, PHYSICAL_FITNESS, CO_CURRICULAR, MIA_HABITS.
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class AssessmentArea(BaseModel):
    """
    Area within an assessment type.
    e.g. Under SOCIAL_EMOTIONAL: "Respectfulness", "Obedience".
    """
    assessment_type = models.ForeignKey(
        AssessmentType,
        on_delete=models.CASCADE,
        related_name="areas",
    )
    name = models.CharField(max_length=200)
    order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Display order within assessment type.",
    )

    class Meta:
        ordering = ["assessment_type", "order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["assessment_type", "name"],
                condition=models.Q(is_deleted=False),
                name="unique_active_assessment_area",
            ),
        ]

    def __str__(self):
        return f"{self.assessment_type.name} → {self.name}"


class AssessmentSubArea(BaseModel):
    """
    Sub-area within an assessment area.
    e.g. Under "Physical Growth": "Strength", "Flexibility", "Speed".
    """
    area = models.ForeignKey(
        AssessmentArea,
        on_delete=models.CASCADE,
        related_name="sub_areas",
    )
    name = models.CharField(max_length=200)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["area", "order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["area", "name"],
                condition=models.Q(is_deleted=False),
                name="unique_active_assessment_sub_area",
            ),
        ]

    def __str__(self):
        return f"{self.area.name} → {self.name}"


class AssessmentCriteria(BaseModel):
    """
    Specific criteria for scoring within a sub-area.
    e.g. "Greets teachers and peers", "Uses polite language".
    """
    sub_area = models.ForeignKey(
        AssessmentSubArea,
        on_delete=models.CASCADE,
        related_name="criteria",
    )
    description = models.TextField()
    max_score = models.PositiveSmallIntegerField(
        default=5,
        help_text="Maximum score for this criteria.",
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name_plural = "assessment criteria"
        ordering = ["sub_area", "order"]

    def __str__(self):
        return f"{self.sub_area.name}: {self.description[:50]}"


class StudentAssessment(BranchScopedModel):
    """
    A student's assessment for a specific type in a specific quarter.
    Only one per (student, quarter, assessment_type).
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"

    student = models.ForeignKey(
        "accounts.Student",
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    academic_year = models.ForeignKey(
        "core.AcademicYear",
        on_delete=models.PROTECT,
        related_name="student_assessments",
    )
    quarter = models.ForeignKey(
        "core.Quarter",
        on_delete=models.PROTECT,
        related_name="student_assessments",
    )
    assessment_type = models.ForeignKey(
        AssessmentType,
        on_delete=models.PROTECT,
        related_name="student_assessments",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="submitted_assessments",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_assessments",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "quarter", "assessment_type"],
                condition=models.Q(is_deleted=False),
                name="unique_student_quarter_assessment",
            ),
        ]
        indexes = [
            models.Index(
                fields=["student", "quarter"],
                condition=models.Q(is_deleted=False),
                name="assmt_stu_qtr_idx",
            ),
            models.Index(
                fields=["branch", "academic_year", "quarter"],
                condition=models.Q(is_deleted=False),
                name="assmt_branch_yr_qtr_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.student} - {self.assessment_type.name} "
            f"({self.quarter}) [{self.status}]"
        )


class StudentAssessmentScore(BaseModel):
    """
    Individual score for a criteria within a student's assessment.
    """
    student_assessment = models.ForeignKey(
        StudentAssessment,
        on_delete=models.CASCADE,
        related_name="scores",
    )
    criteria = models.ForeignKey(
        AssessmentCriteria,
        on_delete=models.PROTECT,
        related_name="scores",
    )
    score = models.PositiveSmallIntegerField(
        help_text="Numeric score (0 to criteria.max_score).",
    )
    remarks = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student_assessment", "criteria"],
                condition=models.Q(is_deleted=False),
                name="unique_active_assessment_score",
            ),
        ]
        indexes = [
            models.Index(
                fields=["student_assessment", "criteria"],
                condition=models.Q(is_deleted=False),
                name="score_assmt_crit_idx",
            ),
        ]

    def clean(self):
        if self.score is not None and self.criteria_id:
            if self.score > self.criteria.max_score:
                raise ValidationError(
                    f"Score ({self.score}) cannot exceed max_score "
                    f"({self.criteria.max_score})."
                )

    def __str__(self):
        return f"{self.student_assessment} → {self.criteria}: {self.score}"
