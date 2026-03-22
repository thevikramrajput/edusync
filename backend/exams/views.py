"""
EduSync — Exams Views.
ExamType (global CRUD), Exam (branch-scoped CRUD),
ExamMark (CRUD + bulk create + report card).
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.viewsets import BaseBranchScopedViewSet
from exams.models import ExamType, Exam, ExamMark
from exams.serializers import (
    ExamTypeSerializer,
    ExamListSerializer,
    ExamCreateSerializer,
    ExamMarkSerializer,
    ExamMarkBulkCreateSerializer,
    ExamMarkUpdateSerializer,
    ReportCardSummarySerializer,
)
from exams import services as exam_services


# ─── ExamType (Global — not branch-scoped) ──────────────────

class ExamTypeViewSet(viewsets.ModelViewSet):
    """
    CRUD for exam types. Global — same across all branches.
    """
    queryset = ExamType.objects.filter(is_deleted=False)
    serializer_class = ExamTypeSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]
    ordering = ["order"]


# ─── Exam (Branch-scoped) ──────────────────────────────────

class ExamViewSet(BaseBranchScopedViewSet):
    """
    CRUD for specific exam instances.
    Branch-scoped — users see exams for their branch only.
    """
    queryset = Exam.objects.all()
    filterset_fields = ["exam_type", "academic_year", "class_assigned"]
    search_fields = ["exam_type__name"]
    ordering = ["-start_date"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ExamCreateSerializer
        return ExamListSerializer

    def get_queryset(self):
        return super().get_queryset().select_related(
            "exam_type", "academic_year", "class_assigned", "branch",
        )


# ─── ExamMark (via Exam's branch) ──────────────────────────

class ExamMarkViewSet(BaseBranchScopedViewSet):
    """
    CRUD + bulk submit + report card for exam marks.

    Endpoints:
        GET    /api/v1/exams/marks/              → list
        POST   /api/v1/exams/marks/              → single create
        GET    /api/v1/exams/marks/{id}/          → retrieve
        PUT    /api/v1/exams/marks/{id}/          → update (row-locked)
        DELETE /api/v1/exams/marks/{id}/          → soft delete
        POST   /api/v1/exams/marks/bulk/          → bulk submit marks
        GET    /api/v1/exams/marks/report-card/   → report card summary
    """
    queryset = ExamMark.objects.all()
    filterset_fields = ["student", "exam", "subject"]
    search_fields = ["student__user__first_name", "student__admission_number"]
    ordering = ["student__admission_number", "subject__name"]

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return ExamMarkUpdateSerializer
        return ExamMarkSerializer

    def get_queryset(self):
        """Filter by exam's branch since ExamMark doesn't have direct branch FK."""
        qs = ExamMark.objects.filter(is_deleted=False).select_related(
            "student__user", "exam__branch", "exam__exam_type", "subject",
        )
        if self.branch_id:
            qs = qs.filter(exam__branch_id=self.branch_id)
        return qs

    def update(self, request, *args, **kwargs):
        """Update with row-level locking via service layer."""
        mark = self.get_object()
        serializer = ExamMarkUpdateSerializer(mark, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated_mark = exam_services.update_exam_mark(
            mark_id=mark.pk,
            marks_obtained=serializer.validated_data["marks_obtained"],
            max_marks=serializer.validated_data["max_marks"],
            updated_by=request.user,
        )

        return Response({
            "success": True,
            "data": ExamMarkSerializer(updated_mark).data,
        })

    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk_create(self, request):
        """
        POST /api/v1/exams/marks/bulk/
        Bulk submit marks with atomic transaction + audit logging.
        """
        serializer = ExamMarkBulkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            created = exam_services.submit_exam_marks(
                exam_id=serializer.validated_data["exam_id"],
                marks_data=serializer.validated_data["marks"],
                submitted_by=request.user,
            )
        except ValueError as e:
            return Response(
                {"success": False, "error_code": "validation_error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": f"{len(created)} marks submitted successfully.",
                "count": len(created),
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="report-card")
    def report_card(self, request):
        """
        GET /api/v1/exams/marks/report-card/?student_id=...&exam_id=...
        Returns annotated report card with totals, percentage, and grade.
        """
        student_id = request.query_params.get("student_id")
        exam_id = request.query_params.get("exam_id")

        if not student_id or not exam_id:
            return Response(
                {
                    "success": False,
                    "error_code": "missing_params",
                    "message": "Both student_id and exam_id are required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            report = exam_services.get_report_card(
                student_id=student_id,
                exam_id=exam_id,
            )
        except Exception as e:
            return Response(
                {"success": False, "error_code": "not_found", "message": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ReportCardSummarySerializer(report)
        return Response({"success": True, "data": serializer.data})
