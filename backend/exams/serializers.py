"""
EduSync — Exams Serializers.
ExamType, Exam, ExamMark (read/bulk write), ReportCard (annotated).
"""
from rest_framework import serializers
from exams.models import ExamType, Exam, ExamMark


# ─── ExamType ───────────────────────────────────────────────

class ExamTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamType
        fields = ["id", "name", "order"]
        read_only_fields = ["id"]


# ─── Exam ───────────────────────────────────────────────────

class ExamListSerializer(serializers.ModelSerializer):
    exam_type_name = serializers.CharField(source="exam_type.name", read_only=True)
    class_name = serializers.CharField(source="class_assigned.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Exam
        fields = [
            "id", "exam_type", "exam_type_name",
            "academic_year",
            "class_assigned", "class_name",
            "branch", "branch_name",
            "start_date", "end_date",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class ExamCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = [
            "exam_type", "academic_year",
            "class_assigned", "start_date", "end_date",
        ]


# ─── ExamMark ───────────────────────────────────────────────

class ExamMarkSerializer(serializers.ModelSerializer):
    """Read serializer — nested student and subject names."""
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    admission_number = serializers.CharField(source="student.admission_number", read_only=True)

    class Meta:
        model = ExamMark
        fields = [
            "id", "student", "student_name", "admission_number",
            "exam", "subject", "subject_name",
            "marks_obtained", "max_marks",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class SingleExamMarkSerializer(serializers.Serializer):
    """One mark entry inside a bulk submission."""
    student_id = serializers.UUIDField()
    subject_id = serializers.UUIDField()
    marks_obtained = serializers.DecimalField(max_digits=6, decimal_places=2)
    max_marks = serializers.DecimalField(max_digits=6, decimal_places=2)

    def validate(self, data):
        if data["marks_obtained"] > data["max_marks"]:
            raise serializers.ValidationError(
                "marks_obtained cannot exceed max_marks."
            )
        if data["marks_obtained"] < 0:
            raise serializers.ValidationError(
                "marks_obtained cannot be negative."
            )
        return data


class ExamMarkBulkCreateSerializer(serializers.Serializer):
    """
    Bulk exam mark submission.
    POST /api/v1/exams/marks/bulk/
    Body: {"exam_id": "...", "marks": [{student_id, subject_id, marks_obtained, max_marks}, ...]}
    """
    exam_id = serializers.UUIDField()
    marks = SingleExamMarkSerializer(many=True, min_length=1)

    def validate_exam_id(self, value):
        from exams.models import Exam
        if not Exam.objects.filter(pk=value, is_deleted=False).exists():
            raise serializers.ValidationError("Exam not found.")
        return value


class ExamMarkUpdateSerializer(serializers.ModelSerializer):
    """Update serializer for individual mark (with row-level locking)."""
    class Meta:
        model = ExamMark
        fields = ["marks_obtained", "max_marks"]


# ─── Report Card (Annotated) ────────────────────────────────

class ReportCardEntrySerializer(serializers.Serializer):
    """Single subject entry in a report card."""
    subject_name = serializers.CharField()
    marks_obtained = serializers.DecimalField(max_digits=6, decimal_places=2)
    max_marks = serializers.DecimalField(max_digits=6, decimal_places=2)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class ReportCardSummarySerializer(serializers.Serializer):
    """Full report card for a student + exam."""
    student_name = serializers.CharField()
    admission_number = serializers.CharField()
    exam_name = serializers.CharField()
    subjects = ReportCardEntrySerializer(many=True)
    total_obtained = serializers.DecimalField(max_digits=8, decimal_places=2)
    total_max = serializers.DecimalField(max_digits=8, decimal_places=2)
    overall_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    grade = serializers.CharField()
