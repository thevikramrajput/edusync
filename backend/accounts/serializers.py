"""
EduSync — Accounts Serializers.
Auth, User profile, Student CRUD, Faculty (read), Role.
"""
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from core.models import Branch
from accounts.models import Role, Faculty, Student

User = get_user_model()


# ─── Auth / Profile ─────────────────────────────────────────

class BranchMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "full_name"]


class CurrentUserSerializer(serializers.ModelSerializer):
    """Read-only serializer for the authenticated user's profile."""
    branch = BranchMinimalSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name",
            "phone", "role_type", "branch", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


# ─── Role ───────────────────────────────────────────────────

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "description"]
        read_only_fields = ["id"]


# ─── Student ────────────────────────────────────────────────

class StudentUserSerializer(serializers.ModelSerializer):
    """Nested user info for student read responses."""
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone"]


class StudentListSerializer(serializers.ModelSerializer):
    """Read serializer — nested user, branch, class, section."""
    user = StudentUserSerializer(read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    class_name = serializers.CharField(source="class_assigned.name", read_only=True)
    section_name = serializers.CharField(source="section.name", read_only=True)
    house_name = serializers.CharField(source="house.name", read_only=True, default=None)

    class Meta:
        model = Student
        fields = [
            "id", "user", "admission_number",
            "branch", "branch_name",
            "class_assigned", "class_name",
            "section", "section_name",
            "house", "house_name",
            "date_of_birth",
            "father_name", "father_phone", "father_occupation",
            "mother_name", "mother_phone", "mother_occupation",
            "address", "aadhar_number",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = fields


class StudentCreateSerializer(serializers.Serializer):
    """
    Write serializer — creates User + Student atomically.
    Uses service layer for atomic creation + audit logging.
    """
    # User fields
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=15, required=False, default="")
    password = serializers.CharField(write_only=True, min_length=8)

    # Student fields
    admission_number = serializers.CharField(max_length=30)
    class_assigned = serializers.PrimaryKeyRelatedField(
        queryset=Student.class_assigned.field.related_model.objects.all()
    )
    section = serializers.PrimaryKeyRelatedField(
        queryset=Student.section.field.related_model.objects.all()
    )
    house = serializers.PrimaryKeyRelatedField(
        queryset=Student.house.field.related_model.objects.all(),
        required=False,
        allow_null=True,
    )
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    father_name = serializers.CharField(max_length=200, required=False, default="")
    father_phone = serializers.CharField(max_length=15, required=False, default="")
    father_occupation = serializers.CharField(max_length=100, required=False, default="")
    mother_name = serializers.CharField(max_length=200, required=False, default="")
    mother_phone = serializers.CharField(max_length=15, required=False, default="")
    mother_occupation = serializers.CharField(max_length=100, required=False, default="")
    address = serializers.CharField(required=False, default="")
    aadhar_number = serializers.CharField(max_length=20, required=False, default="")

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class StudentUpdateSerializer(serializers.ModelSerializer):
    """
    Update serializer — updates Student fields only.
    User fields (email, name) updated via separate profile endpoint.
    """
    class Meta:
        model = Student
        fields = [
            "admission_number",
            "class_assigned", "section", "house",
            "date_of_birth",
            "father_name", "father_phone", "father_occupation",
            "mother_name", "mother_phone", "mother_occupation",
            "address", "aadhar_number",
        ]
