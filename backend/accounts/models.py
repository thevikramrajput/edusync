"""
EduSync — Accounts Models.
Custom User, Faculty, Student, Parent, Role, FacultyRoleMapping, RolePermission.
"""
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from common.models import BaseModel, BranchScopedModel
from common.managers import SoftDeleteManager, AllObjectsManager


# ─── Custom User Manager ────────────────────────────────────

class CustomUserManager(BaseUserManager):
    """
    Custom manager for User model with email as USERNAME_FIELD.
    Soft-delete aware — excluded deleted users from authentication.
    """

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role_type", User.RoleType.SUPER_ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


# ─── Custom User Model ──────────────────────────────────────

class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Custom User model with email login.
    Every person in the system (admin, faculty, student, parent) has a User record.
    """

    class RoleType(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        SCHOOL_ADMIN = "SCHOOL_ADMIN", "School Admin"
        FACULTY = "FACULTY", "Faculty"
        STUDENT = "STUDENT", "Student"
        PARENT = "PARENT", "Parent"

    email = models.EmailField(
        unique=True,
        help_text="Login email — must be unique across the system.",
    )
    phone = models.CharField(max_length=15, blank=True, default="")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role_type = models.CharField(
        max_length=20,
        choices=RoleType.choices,
    )
    branch = models.ForeignKey(
        "core.Branch",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="users",
        help_text="Branch this user belongs to. NULL for super admins.",
    )
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "role_type"]

    objects = CustomUserManager()
    all_objects = AllObjectsManager()

    class Meta:
        indexes = [
            models.Index(fields=["role_type"]),
            models.Index(fields=["branch", "role_type"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


# ─── Role ────────────────────────────────────────────────────

class Role(BaseModel):
    """
    System roles: DIRECTOR, PRINCIPAL, HOD, SECTION_INCHARGE, etc.
    Mapped to faculty via FacultyRoleMapping.
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="e.g. DIRECTOR, PRINCIPAL, HOD, SECTION_INCHARGE",
    )
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# ─── Faculty ────────────────────────────────────────────────

class Faculty(BranchScopedModel):
    """
    Faculty profile linked to a User.
    Contains professional details — level, grade, faculty code.
    """

    class Level(models.TextChoices):
        L1 = "L1", "Level 1 (Principal, Heads)"
        L2 = "L2", "Level 2 (HODs, Incharges)"
        L3 = "L3", "Level 3 (Subject Teachers)"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="faculty_profile",
    )
    faculty_code = models.CharField(max_length=20)
    level = models.CharField(max_length=5, choices=Level.choices)
    grade = models.CharField(max_length=10, blank=True, default="")
    joining_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "faculty"
        constraints = [
            models.UniqueConstraint(
                fields=["faculty_code", "branch"],
                condition=models.Q(is_deleted=False),
                name="unique_active_faculty_per_branch",
            ),
        ]
        indexes = [
            models.Index(fields=["branch", "level"]),
        ]

    def __str__(self):
        return f"{self.user.full_name} ({self.faculty_code})"


# ─── Faculty Role Mapping ───────────────────────────────────

class FacultyRoleMapping(BaseModel):
    """
    Maps a faculty member to specific roles with scope.
    One faculty can have multiple roles (HOD + Section Incharge, etc.)
    scope_type determines data visibility (BRANCH or GLOBAL).
    """

    class ScopeType(models.TextChoices):
        BRANCH = "BRANCH", "Branch Only"
        GLOBAL = "GLOBAL", "All Branches"

    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name="role_mappings",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="faculty_mappings",
    )
    branch = models.ForeignKey(
        "core.Branch",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        help_text="NULL for GLOBAL scope roles.",
    )
    scope_type = models.CharField(
        max_length=10,
        choices=ScopeType.choices,
        default=ScopeType.BRANCH,
    )
    class_assigned = models.ForeignKey(
        "academics.Class",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="role_mappings",
        help_text="Class scope (e.g., Section Incharge for Class 10).",
    )
    section = models.ForeignKey(
        "academics.Section",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="role_mappings",
    )
    subject = models.ForeignKey(
        "academics.Subject",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="role_mappings",
        help_text="Subject scope (e.g., HOD for Physics).",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "faculty", "role", "branch", "subject",
                    "class_assigned", "section",
                ],
                condition=models.Q(is_deleted=False),
                name="unique_active_faculty_role_mapping",
            ),
        ]

    def __str__(self):
        return f"{self.faculty} → {self.role.name} ({self.scope_type})"


# ─── Role Permission ────────────────────────────────────────

class RolePermission(BaseModel):
    """
    Configurable permission keys per role.
    Controls API-level access. Admin-editable for future flexibility.
    """
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="permissions",
    )
    permission_key = models.CharField(
        max_length=100,
        help_text="e.g. can_mark_attendance, can_upload_marks",
    )
    branch_scope_allowed = models.BooleanField(
        default=False,
        help_text="If True, this role can see cross-branch data.",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission_key"],
                condition=models.Q(is_deleted=False),
                name="unique_active_role_permission",
            ),
        ]

    def __str__(self):
        return f"{self.role.name} → {self.permission_key}"


# ─── Student ────────────────────────────────────────────────

class Student(BranchScopedModel):
    """
    Student profile linked to a User.
    Contains academic placement and personal details.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    admission_number = models.CharField(max_length=30)
    class_assigned = models.ForeignKey(
        "academics.Class",
        on_delete=models.PROTECT,
        related_name="students",
    )
    section = models.ForeignKey(
        "academics.Section",
        on_delete=models.PROTECT,
        related_name="students",
    )
    house = models.ForeignKey(
        "academics.House",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="students",
    )
    date_of_birth = models.DateField(null=True, blank=True)
    father_name = models.CharField(max_length=200, blank=True, default="")
    father_phone = models.CharField(max_length=15, blank=True, default="")
    father_occupation = models.CharField(max_length=100, blank=True, default="")
    mother_name = models.CharField(max_length=200, blank=True, default="")
    mother_phone = models.CharField(max_length=15, blank=True, default="")
    mother_occupation = models.CharField(max_length=100, blank=True, default="")
    address = models.TextField(blank=True, default="")
    aadhar_number = models.CharField(max_length=20, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["admission_number", "branch"],
                condition=models.Q(is_deleted=False),
                name="unique_active_admission_per_branch",
            ),
        ]
        indexes = [
            models.Index(
                fields=["branch", "class_assigned", "section"],
                condition=models.Q(is_deleted=False),
                name="stu_branch_cls_sec_idx",
            ),
        ]

    def __str__(self):
        return f"{self.user.full_name} ({self.admission_number})"


# ─── Parent ──────────────────────────────────────────────────

class Parent(BaseModel):
    """
    Parent profile linked to a User.
    Can have multiple children (students) across branches.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="parent_profile",
    )
    children = models.ManyToManyField(
        Student,
        through="ParentStudentMapping",
        related_name="parents",
        blank=True,
    )

    def __str__(self):
        return f"Parent: {self.user.full_name}"


class ParentStudentMapping(BaseModel):
    """
    Explicit through table for Parent→Student M2M.
    Allows soft-delete and audit tracking on the relationship.
    """
    parent = models.ForeignKey(
        Parent,
        on_delete=models.CASCADE,
        related_name="student_mappings",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="parent_mappings",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "student"],
                condition=models.Q(is_deleted=False),
                name="unique_active_parent_student",
            ),
        ]

    def __str__(self):
        return f"{self.parent} → {self.student}"
