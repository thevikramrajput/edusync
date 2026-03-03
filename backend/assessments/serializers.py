"""
EduSync — Assessments Serializers.
Nested reads, flat writes, bulk scores, quarterly summary.
"""
from rest_framework import serializers
from assessments.models import (
    AssessmentType,
    AssessmentArea,
    AssessmentSubArea,
    AssessmentCriteria,
    StudentAssessment,
    StudentAssessmentScore,
)


# ─── Lookup Serializers (Read-Only) ─────────────────────────

class AssessmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentType
        fields = ["id", "name", "description"]
        read_only_fields = ["id"]


class AssessmentCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentCriteria
        fields = ["id", "description", "max_score", "order"]
        read_only_fields = fields


class AssessmentSubAreaSerializer(serializers.ModelSerializer):
    criteria = AssessmentCriteriaSerializer(many=True, read_only=True)

    class Meta:
        model = AssessmentSubArea
        fields = ["id", "name", "order", "criteria"]
        read_only_fields = fields


class AssessmentAreaSerializer(serializers.ModelSerializer):
    sub_areas = AssessmentSubAreaSerializer(many=True, read_only=True)

    class Meta:
        model = AssessmentArea
        fields = ["id", "name", "order", "sub_areas"]
        read_only_fields = fields


class AssessmentTypeDetailSerializer(serializers.ModelSerializer):
    """Full nested tree: Type → Areas → SubAreas → Criteria."""
    areas = AssessmentAreaSerializer(many=True, read_only=True)

    class Meta:
        model = AssessmentType
        fields = ["id", "name", "description", "areas"]
        read_only_fields = fields


# ─── Score Serializers ──────────────────────────────────────

class ScoreReadSerializer(serializers.ModelSerializer):
    """Score with nested criteria details."""
    criteria_description = serializers.CharField(
        source="criteria.description", read_only=True,
    )
    max_score = serializers.IntegerField(
        source="criteria.max_score", read_only=True,
    )

    class Meta:
        model = StudentAssessmentScore
        fields = [
            "id", "criteria", "criteria_description",
            "score", "max_score", "remarks",
        ]
        read_only_fields = fields


class ScoreWriteSerializer(serializers.Serializer):
    """Single score entry for bulk submission."""
    criteria_id = serializers.UUIDField()
    score = serializers.IntegerField(min_value=0)
    remarks = serializers.CharField(required=False, default="", allow_blank=True)


# ─── StudentAssessment Serializers ──────────────────────────

class StudentAssessmentListSerializer(serializers.ModelSerializer):
    """Read serializer with nested names."""
    student_name = serializers.CharField(
        source="student.user.full_name", read_only=True,
    )
    admission_number = serializers.CharField(
        source="student.admission_number", read_only=True,
    )
    assessment_type_name = serializers.CharField(
        source="assessment_type.name", read_only=True,
    )
    quarter_name = serializers.CharField(
        source="quarter.name", read_only=True,
    )
    scores = ScoreReadSerializer(many=True, read_only=True)

    class Meta:
        model = StudentAssessment
        fields = [
            "id", "student", "student_name", "admission_number",
            "academic_year", "quarter", "quarter_name",
            "assessment_type", "assessment_type_name",
            "status", "submitted_by", "approved_by",
            "scores",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class StudentAssessmentCreateSerializer(serializers.ModelSerializer):
    """Create serializer — scores submitted separately via service."""
    scores = ScoreWriteSerializer(many=True, required=False)

    class Meta:
        model = StudentAssessment
        fields = [
            "student", "academic_year", "quarter",
            "assessment_type", "scores",
        ]

    def validate(self, data):
        # Scores max_score validation happens in service layer
        return data


# ─── Quarterly Summary ──────────────────────────────────────

class QuarterlyAssessmentSummarySerializer(serializers.Serializer):
    """Aggregated summary for a student in a quarter."""
    assessment_type_name = serializers.CharField()
    total_score = serializers.IntegerField()
    total_max_score = serializers.IntegerField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    status = serializers.CharField()
    score_count = serializers.IntegerField()
