"""
EduSync — Academics Models.
Class, Section, Subject, House, FacultySubjectMapping.
"""
from django.db import models
from common.models import BranchScopedModel, BaseModel


class Class(BranchScopedModel):
    """
    School class within a branch (e.g., 6th, 7th, 8th).
    """
    name = models.CharField(
        max_length=20,
        help_text="e.g. 6th, 7th, 8th, 9th, 10th",
    )

    class Meta:
        verbose_name_plural = "classes"
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "name"],
                condition=models.Q(is_deleted=False),
                name="unique_active_class_per_branch",
            ),
        ]
        indexes = [
            models.Index(fields=["branch"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.branch.name})"


class Section(BaseModel):
    """
    Section within a class (e.g., A, B, C).
    """
    class_ref = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    name = models.CharField(
        max_length=10,
        help_text="e.g. A, B, C",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["class_ref", "name"],
                condition=models.Q(is_deleted=False),
                name="unique_active_section_per_class",
            ),
        ]

    def __str__(self):
        return f"{self.class_ref} - {self.name}"


class Subject(BranchScopedModel):
    """
    Academic subject within a branch (e.g., Mathematics, English).
    """
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "name"],
                condition=models.Q(is_deleted=False),
                name="unique_active_subject_per_branch",
            ),
        ]
        indexes = [
            models.Index(fields=["branch"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.branch.name})"


class House(BranchScopedModel):
    """
    Student house for inter-house competitions.
    """
    name = models.CharField(max_length=50)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "name"],
                condition=models.Q(is_deleted=False),
                name="unique_active_house_per_branch",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.branch.name})"


class FacultySubjectMapping(BaseModel):
    """
    Maps faculty to subjects they teach in specific class-section combinations.
    One teacher can teach multiple subjects; one subject can have multiple teachers.
    """
    faculty = models.ForeignKey(
        "accounts.Faculty",
        on_delete=models.CASCADE,
        related_name="subject_mappings",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="faculty_mappings",
    )
    class_assigned = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name="faculty_subject_mappings",
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="faculty_subject_mappings",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["faculty", "subject", "class_assigned", "section"],
                condition=models.Q(is_deleted=False),
                name="unique_active_faculty_subject_class_section",
            ),
        ]
        indexes = [
            models.Index(fields=["class_assigned", "section"]),
        ]

    def __str__(self):
        return f"{self.faculty} → {self.subject} ({self.class_assigned}-{self.section})"
