"""
EduSync — Parent Feedback System.
Quarter-based feedback collected during PTMs.
"""
from django.db import models
from common.models import BaseModel


class ParentFeedbackQuestion(BaseModel):
    """
    Predefined feedback questions for parents.
    e.g. Study hours, Routine, Mobile usage.
    """
    question_text = models.TextField()
    category = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="e.g. Study Habits, Routine, Digital Usage",
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "category"]

    def __str__(self):
        return self.question_text[:80]


class ParentFeedbackResponse(BaseModel):
    """
    Parent's response to a feedback question for a specific student/quarter.
    """
    student = models.ForeignKey(
        "accounts.Student",
        on_delete=models.CASCADE,
        related_name="parent_feedback",
    )
    academic_year = models.ForeignKey(
        "core.AcademicYear",
        on_delete=models.PROTECT,
        related_name="parent_feedback",
    )
    quarter = models.ForeignKey(
        "core.Quarter",
        on_delete=models.PROTECT,
        related_name="parent_feedback",
    )
    question = models.ForeignKey(
        ParentFeedbackQuestion,
        on_delete=models.PROTECT,
        related_name="responses",
    )
    response_text = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "quarter", "question"],
                condition=models.Q(is_deleted=False),
                name="unique_active_parent_feedback_response",
            ),
        ]

    def __str__(self):
        return f"{self.student} - {self.question.question_text[:40]} ({self.quarter})"
