"""
EduSync — Exam Engine.
ExamType, Exam, ExamMark. Percentages and grades computed dynamically.
"""
from django.db import models
from common.models import BaseModel, BranchScopedModel


class ExamType(BaseModel):
    """
    Type of exam: MT-1, Pre-Mid, Mid Term, MT-2, Post-Mid, Annual.
    Global — same for all branches.
    """
    name = models.CharField(max_length=50, unique=True)
    order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Display order in academic calendar.",
    )

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Exam(BranchScopedModel):
    """
    Specific exam instance for a class in a branch.
    """
    exam_type = models.ForeignKey(
        ExamType,
        on_delete=models.PROTECT,
        related_name="exams",
    )
    academic_year = models.ForeignKey(
        "core.AcademicYear",
        on_delete=models.PROTECT,
        related_name="exams",
    )
    class_assigned = models.ForeignKey(
        "academics.Class",
        on_delete=models.PROTECT,
        related_name="exams",
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["exam_type", "academic_year", "branch", "class_assigned"],
                condition=models.Q(is_deleted=False),
                name="unique_active_exam_per_class",
            ),
        ]
        indexes = [
            models.Index(
                fields=["branch", "academic_year"],
                condition=models.Q(is_deleted=False),
                name="exam_branch_year_idx",
            ),
        ]

    def __str__(self):
        return f"{self.exam_type.name} - {self.class_assigned} ({self.academic_year})"


class ExamMark(BaseModel):
    """
    Individual mark entry: one student, one exam, one subject.
    Percentages and grades computed via DB annotation, not stored.
    """
    student = models.ForeignKey(
        "accounts.Student",
        on_delete=models.CASCADE,
        related_name="exam_marks",
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="marks",
    )
    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.PROTECT,
        related_name="exam_marks",
    )
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2)
    max_marks = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "exam", "subject"],
                condition=models.Q(is_deleted=False),
                name="unique_student_exam_subject_mark",
            ),
        ]
        indexes = [
            models.Index(
                fields=["student", "exam"],
                condition=models.Q(is_deleted=False),
                name="mark_stu_exam_idx",
            ),
            models.Index(
                fields=["exam", "subject"],
                condition=models.Q(is_deleted=False),
                name="mark_exam_subj_idx",
            ),
        ]

    def __str__(self):
        return f"{self.student} - {self.subject}: {self.marks_obtained}/{self.max_marks}"
