"""
EduSync — Accounts Views.
CurrentUser profile, StudentViewSet (full CRUD).
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.viewsets import BaseBranchScopedViewSet
from accounts.models import Student
from accounts.serializers import (
    CurrentUserSerializer,
    StudentListSerializer,
    StudentCreateSerializer,
    StudentUpdateSerializer,
)
from accounts import services as account_services


# ─── Current User Profile ───────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    """
    GET /api/v1/auth/me/
    Returns the authenticated user's profile.
    """
    serializer = CurrentUserSerializer(request.user)
    return Response({"success": True, "data": serializer.data})


# ─── Student CRUD ViewSet ───────────────────────────────────

class StudentViewSet(BaseBranchScopedViewSet):
    """
    Full CRUD for students.
    Branch-scoped — users only see students in their branch.
    All write operations go through the service layer.

    Endpoints:
        GET    /api/v1/students/           → list
        POST   /api/v1/students/           → create
        GET    /api/v1/students/{id}/      → retrieve
        PUT    /api/v1/students/{id}/      → update
        PATCH  /api/v1/students/{id}/      → partial update
        DELETE /api/v1/students/{id}/      → soft delete
    """
    queryset = Student.objects.all()
    filterset_fields = ["class_assigned", "section", "house", "is_active"]
    search_fields = [
        "user__first_name", "user__last_name",
        "admission_number", "user__email",
    ]
    ordering_fields = [
        "admission_number", "user__first_name",
        "created_at", "class_assigned__name",
    ]
    ordering = ["admission_number"]

    def get_serializer_class(self):
        if self.action == "create":
            return StudentCreateSerializer
        if self.action in ("update", "partial_update"):
            return StudentUpdateSerializer
        return StudentListSerializer

    def get_queryset(self):
        return super().get_queryset().select_related(
            "user", "branch", "class_assigned", "section", "house",
        )

    def create(self, request, *args, **kwargs):
        """Create student via service layer (atomic User + Student)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student = account_services.create_student(
            validated_data=serializer.validated_data,
            branch=request.user.branch,
            created_by=request.user,
        )

        return Response(
            {
                "success": True,
                "data": StudentListSerializer(student).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        """Update student via service layer (with audit)."""
        partial = kwargs.pop("partial", False)
        student = self.get_object()
        serializer = self.get_serializer(student, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        student = account_services.update_student(
            student=student,
            validated_data=serializer.validated_data,
            updated_by=request.user,
        )

        return Response({
            "success": True,
            "data": StudentListSerializer(student).data,
        })

    def destroy(self, request, *args, **kwargs):
        """Soft delete student via service layer."""
        student = self.get_object()
        account_services.soft_delete_student(
            student=student,
            deleted_by=request.user,
        )
        return Response(
            {"success": True, "message": "Student deleted successfully."},
            status=status.HTTP_200_OK,
        )
