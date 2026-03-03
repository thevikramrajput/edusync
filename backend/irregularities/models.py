"""
EduSync — Irregularity Tracking Engine.
Date-wise tracking by section incharges and subject teachers.
Monthly/quarterly totals computed dynamically via queries.
"""
from django.db import models
from common.models import BaseModel, BranchScopedModel


class IrregularityType(BaseModel):
    """
    Type of irregularity and who reports it.
    e.g. Leave (SECTION_INCHARGE), HW Pendency (SUBJECT_TEACHER).
    """

    class ApplicableRole(models.TextChoices):
        SECTION_INCHARGE = "SECTION_INCHARGE", "Section Incharge"
        SUBJECT_TEACHER = "SUBJECT_TEACHER", "Subject Teacher"

    name = models.CharField(max_length=100)
    applicable_role = models.CharField(
        max_length=20,
        choices=ApplicableRole.choices,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name"],
                condition=models.Q(is_deleted=False),
                name="unique_active_irregularity_type",
            ),
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.applicable_role})"


class StudentIrregularity(BranchScopedModel):
    """
    Individual irregularity entry for a student on a specific date.
    Totals per month/quarter are COMPUTED via annotated queries, never stored.
    """
    student = models.ForeignKey(
        "accounts.Student",
        on_delete=models.CASCADE,
        related_name="irregularities",
    )
    academic_year = models.ForeignKey(
        "core.AcademicYear",
        on_delete=models.PROTECT,
        related_name="irregularities",
    )
    quarter = models.ForeignKey(
        "core.Quarter",
        on_delete=models.PROTECT,
        related_name="irregularities",
    )
    month = models.PositiveSmallIntegerField(
        help_text="Month number (1-12).",
    )
    date = models.DateField()
    irregularity_type = models.ForeignKey(
        IrregularityType,
        on_delete=models.PROTECT,
        related_name="entries",
    )
    subject = models.ForeignKey(
        "academics.Subject",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="irregularities",
        help_text="Subject (only for SUBJECT_TEACHER irregularities).",
    )
    reported_by = models.ForeignKey(
        "accounts.Faculty",
        on_delete=models.PROTECT,
        related_name="reported_irregularities",
    )

    class Meta:
        verbose_name_plural = "student irregularities"
        indexes = [
            models.Index(
                fields=["student", "date"],
                condition=models.Q(is_deleted=False),
                name="irreg_stu_date_idx",
            ),
            models.Index(
                fields=["branch", "quarter", "month"],
                condition=models.Q(is_deleted=False),
                name="irreg_branch_qtr_mon_idx",
            ),
        ]

    def __str__(self):
        return f"{self.student} - {self.irregularity_type.name} ({self.date})"
