"""
EduSync — Accounts Service Layer.
Atomic operations for Student and Faculty creation with audit logging.
"""
import logging
from django.db import transaction
from django.contrib.auth import get_user_model

from accounts.models import Student
from common.services import audit_log

logger = logging.getLogger("edusync.audit")
User = get_user_model()


@transaction.atomic
def create_student(*, validated_data, branch, created_by=None):
    """
    Atomically create a User + Student pair.
    Rolls back both if either fails.

    Args:
        validated_data: dict from StudentCreateSerializer
        branch: Branch instance (auto-injected by ViewSet)
        created_by: User performing the action (for audit)

    Returns:
        Student instance
    """
    # Extract user fields
    user = User.objects.create_user(
        email=validated_data["email"],
        password=validated_data["password"],
        first_name=validated_data["first_name"],
        last_name=validated_data["last_name"],
        phone=validated_data.get("phone", ""),
        role_type=User.RoleType.STUDENT,
        branch=branch,
    )

    # Create student profile
    student = Student.objects.create(
        user=user,
        branch=branch,
        admission_number=validated_data["admission_number"],
        class_assigned=validated_data["class_assigned"],
        section=validated_data["section"],
        house=validated_data.get("house"),
        date_of_birth=validated_data.get("date_of_birth"),
        father_name=validated_data.get("father_name", ""),
        father_phone=validated_data.get("father_phone", ""),
        father_occupation=validated_data.get("father_occupation", ""),
        mother_name=validated_data.get("mother_name", ""),
        mother_phone=validated_data.get("mother_phone", ""),
        mother_occupation=validated_data.get("mother_occupation", ""),
        address=validated_data.get("address", ""),
        aadhar_number=validated_data.get("aadhar_number", ""),
    )

    # Audit log
    audit_log(
        action="CREATE",
        instance=student,
        new_data={
            "user_id": str(user.pk),
            "email": user.email,
            "admission_number": student.admission_number,
            "branch": str(branch.pk),
        },
        user=created_by,
    )

    logger.info(
        f"Student created: {student.admission_number} "
        f"branch={branch.name} by={getattr(created_by, 'email', 'system')}"
    )

    return student


@transaction.atomic
def update_student(*, student, validated_data, updated_by=None):
    """
    Update student with audit logging.

    Args:
        student: Student instance
        validated_data: dict from StudentUpdateSerializer
        updated_by: User performing the action

    Returns:
        Updated Student instance
    """
    old_data = {
        field: str(getattr(student, field))
        for field in validated_data.keys()
    }

    for field, value in validated_data.items():
        setattr(student, field, value)
    student.save()

    new_data = {
        field: str(getattr(student, field))
        for field in validated_data.keys()
    }

    audit_log(
        action="UPDATE",
        instance=student,
        old_data=old_data,
        new_data=new_data,
        user=updated_by,
    )

    return student


@transaction.atomic
def soft_delete_student(*, student, deleted_by=None):
    """
    Soft delete student and linked user.
    """
    # Soft delete user
    student.user.is_deleted = True
    student.user.is_active = False
    student.user.save()

    # Soft delete student profile
    student.delete()  # BaseModel.delete() sets is_deleted=True

    audit_log(
        action="DELETE",
        instance=student,
        old_data={"admission_number": student.admission_number},
        user=deleted_by,
    )

    logger.info(
        f"Student soft-deleted: {student.admission_number} "
        f"by={getattr(deleted_by, 'email', 'system')}"
    )
