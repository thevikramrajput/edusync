"""
EduSync — Core Models.
School, Branch, AcademicYear, Quarter, GradeMapping.
"""
from django.db import models
from django.core.exceptions import ValidationError
from common.models import BaseModel


class School(BaseModel):
    """
    Top-level entity. Enables future multi-school SaaS expansion.
    Currently: 1 school with 3 branches.
    """
    name = models.CharField(max_length=300)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True, default="")
    contact_email = models.EmailField(blank=True, default="")
    contact_phone = models.CharField(max_length=15, blank=True, default="")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Branch(BaseModel):
    """
    Represents a school branch (e.g., CHK, JJR, DADRI).
    Belongs to a School. Central entity — most tables reference this.
    """
    school = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name="branches",
    )
    name = models.CharField(
        max_length=10,
        unique=True,
        help_text="Short code, e.g. CHK, JJR, DADRI",
    )
    full_name = models.CharField(max_length=200)
    address = models.TextField(blank=True, default="")
    code = models.CharField(max_length=10, blank=True, default="")

    class Meta:
        verbose_name_plural = "branches"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.full_name}"


class AcademicYear(BaseModel):
    """
    Represents an academic year (e.g., 2025-26).
    Only one can be marked as current at a time.
    """
    year_label = models.CharField(
        max_length=10,
        unique=True,
        help_text="e.g. 2025-26",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(
        default=False,
        help_text="Only one academic year can be current.",
    )

    class Meta:
        ordering = ["-start_date"]

    def save(self, *args, **kwargs):
        # Enforce only one current academic year
        if self.is_current:
            AcademicYear.objects.filter(is_current=True).exclude(
                pk=self.pk
            ).update(is_current=False)
        super().save(*args, **kwargs)

    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError("Start date must be before end date.")

    def __str__(self):
        return self.year_label


class Quarter(BaseModel):
    """
    Quarter within an academic year (Q1, Q2, Q3, Q4).
    All assessments, irregularities, and feedback are quarter-scoped.
    """
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="quarters",
    )
    name = models.CharField(
        max_length=5,
        help_text="e.g. Q1, Q2, Q3, Q4",
    )
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["academic_year", "name"],
                condition=models.Q(is_deleted=False),
                name="unique_active_quarter_per_year",
            ),
        ]
        ordering = ["academic_year", "name"]

    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError("Start date must be before end date.")

    def __str__(self):
        return f"{self.academic_year} - {self.name}"


class GradeMapping(BaseModel):
    """
    Configurable grade mapping from percentage ranges.
    Seeded via seed_initial_data command. Can be customized per school later.
    """
    min_percentage = models.PositiveSmallIntegerField()
    max_percentage = models.PositiveSmallIntegerField()
    grade = models.CharField(max_length=5)

    class Meta:
        ordering = ["-min_percentage"]
        constraints = [
            models.UniqueConstraint(
                fields=["min_percentage", "max_percentage"],
                condition=models.Q(is_deleted=False),
                name="unique_active_grade_range",
            ),
        ]

    def __str__(self):
        return f"{self.min_percentage}–{self.max_percentage}% → {self.grade}"
