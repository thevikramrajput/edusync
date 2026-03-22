"""
EduSync — Assessments Views.
AssessmentType (global), StudentAssessment (branch-scoped + status actions),
quarterly summary.
"""
from django.core.exceptions import ValidationError

from rest_framework import status as http_status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.viewsets import BaseBranchScopedViewSet
from assessments.models import (
    AssessmentType,
    StudentAssessment,
)
from assessments.serializers import (
    AssessmentTypeSerializer,
    AssessmentTypeDetailSerializer,
    StudentAssessmentListSerializer,
    StudentAssessmentCreateSerializer,
    QuarterlyAssessmentSummarySerializer,
)
from assessments import services as assessment_services


# ─── AssessmentType (Global) ────────────────────────────────

class AssessmentTypeViewSet(viewsets.ModelViewSet):
    """
    CRUD for assessment types (global — same across all branches).
    GET /{id}/ returns the full nested tree (areas → sub_areas → criteria).
    """
    queryset = AssessmentType.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AssessmentTypeDetailSerializer
        return AssessmentTypeSerializer


# ─── StudentAssessment (Branch-scoped) ──────────────────────

class StudentAssessmentViewSet(BaseBranchScopedViewSet):
    """
    CRUD + submit + approve + quarterly summary for student assessments.

    Endpoints:
        GET    /api/v1/assessments/student/            → list
        POST   /api/v1/assessments/student/            → create (with scores)
        GET    /api/v1/assessments/student/{id}/        → retrieve (nested scores)
        POST   /api/v1/assessments/student/{id}/submit/ → DRAFT → SUBMITTED
        POST   /api/v1/assessments/student/{id}/approve/→ SUBMITTED → APPROVED
        GET    /api/v1/assessments/student/quarterly-summary/
    """
    queryset = StudentAssessment.objects.all()
    filterset_fields = ["student", "assessment_type", "quarter", "status"]
    search_fields = [
        "student__user__first_name",
        "student__admission_number",
    ]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action in ("create",):
            return StudentAssessmentCreateSerializer
        return StudentAssessmentListSerializer

    def get_queryset(self):
        return super().get_queryset().select_related(
            "student__user", "assessment_type",
            "quarter", "academic_year", "branch",
        ).prefetch_related("scores__criteria")

    def create(self, request, *args, **kwargs):
        """Create assessment via service layer (atomic + audit)."""
        serializer = StudentAssessmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        branch = request.user.branch
        if self.branch_id:
            from core.models import Branch
            branch = Branch.objects.get(pk=self.branch_id)

        try:
            assessment = assessment_services.create_student_assessment(
                validated_data=serializer.validated_data,
                branch=branch,
                created_by=request.user,
            )
        except ValidationError as e:
            return Response(
                {"success": False, "error_code": "validation_error", "message": str(e)},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "data": StudentAssessmentListSerializer(assessment).data,
            },
            status=http_status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        """POST /api/v1/assessments/student/{id}/submit/ → DRAFT→SUBMITTED."""
        try:
            assessment = assessment_services.submit_assessment(
                assessment_id=pk,
                submitted_by=request.user,
            )
        except ValidationError as e:
            return Response(
                {"success": False, "error_code": "invalid_transition", "message": str(e)},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            "success": True,
            "message": "Assessment submitted successfully.",
            "data": {"id": str(assessment.pk), "status": assessment.status},
        })

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        """POST /api/v1/assessments/student/{id}/approve/ → SUBMITTED→APPROVED."""
        try:
            assessment = assessment_services.approve_assessment(
                assessment_id=pk,
                approved_by=request.user,
            )
        except ValidationError as e:
            return Response(
                {"success": False, "error_code": "invalid_transition", "message": str(e)},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            "success": True,
            "message": "Assessment approved successfully.",
            "data": {"id": str(assessment.pk), "status": assessment.status},
        })

    @action(detail=False, methods=["get"], url_path="quarterly-summary")
    def quarterly_summary(self, request):
        """
        GET /api/v1/assessments/student/quarterly-summary/
            ?student_id=...&quarter_id=...
        """
        student_id = request.query_params.get("student_id")
        quarter_id = request.query_params.get("quarter_id")

        if not student_id or not quarter_id:
            return Response(
                {
                    "success": False,
                    "error_code": "missing_params",
                    "message": "Both student_id and quarter_id are required.",
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        summary = assessment_services.get_quarterly_summary(
            student_id=student_id,
            quarter_id=quarter_id,
        )

        serializer = QuarterlyAssessmentSummarySerializer(summary, many=True)
        return Response({"success": True, "data": serializer.data})
