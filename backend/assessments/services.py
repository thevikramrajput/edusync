"""
EduSync — Assessments Service Layer.
Atomic creation, status transitions, score validation, quarterly summary.
"""
import logging
from decimal import Decimal

from django.db import transaction
from django.core.exceptions import ValidationError

from assessments.models import (
    AssessmentCriteria,
    StudentAssessment,
    StudentAssessmentScore,
)
from common.services import audit_log, audit_bulk_create

logger = logging.getLogger("edusync.audit")


@transaction.atomic
def create_student_assessment(*, validated_data, branch, created_by=None):
    """
    Create a StudentAssessment with optional scores.
    Atomic — all-or-nothing.

    Args:
        validated_data: dict with student, academic_year, quarter,
                        assessment_type, and optional scores list
        branch: Branch instance for branch-scoped creation
        created_by: User performing the action

    Returns:
        Created StudentAssessment instance
    """
    scores_data = validated_data.pop("scores", [])

    assessment = StudentAssessment.objects.create(
        branch=branch,
        status=StudentAssessment.Status.DRAFT,
        **validated_data,
    )

    audit_log(
        action="CREATE",
        instance=assessment,
        new_data={
            "student": str(assessment.student_id),
            "quarter": str(assessment.quarter_id),
            "assessment_type": str(assessment.assessment_type_id),
            "status": assessment.status,
        },
        user=created_by,
    )

    if scores_data:
        _create_scores(
            assessment=assessment,
            scores_data=scores_data,
            user=created_by,
        )

    logger.info(
        f"Assessment created: student={assessment.student_id} "
        f"type={assessment.assessment_type_id} status=DRAFT "
        f"by={getattr(created_by, 'email', 'system')}"
    )

    return assessment


@transaction.atomic
def _create_scores(*, assessment, scores_data, user=None):
    """
    Bulk create scores for an assessment with max_score validation.
    Raises ValidationError if any score exceeds criteria.max_score.
    """
    criteria_ids = [s["criteria_id"] for s in scores_data]
    criteria_map = {
        str(c.pk): c
        for c in AssessmentCriteria.objects.filter(
            pk__in=criteria_ids, is_deleted=False,
        )
    }

    if len(criteria_map) != len(criteria_ids):
        missing = set(str(cid) for cid in criteria_ids) - set(criteria_map.keys())
        raise ValidationError(f"Criteria not found: {missing}")

    score_objects = []
    for s in scores_data:
        criteria = criteria_map[str(s["criteria_id"])]
        if s["score"] > criteria.max_score:
            raise ValidationError(
                f"Score {s['score']} exceeds max_score {criteria.max_score} "
                f"for criteria '{criteria.description[:50]}'."
            )
        score_objects.append(
            StudentAssessmentScore(
                student_assessment=assessment,
                criteria=criteria,
                score=s["score"],
                remarks=s.get("remarks", ""),
            )
        )

    return audit_bulk_create(StudentAssessmentScore, score_objects, user=user)


@transaction.atomic
def submit_assessment(*, assessment_id, submitted_by):
    """
    Transition DRAFT → SUBMITTED.
    Requires at least one score to be present.

    Args:
        assessment_id: UUID
        submitted_by: User performing the action

    Returns:
        Updated StudentAssessment instance

    Raises:
        ValidationError on invalid transition
    """
    assessment = StudentAssessment.objects.select_for_update().get(
        pk=assessment_id, is_deleted=False,
    )

    if assessment.status != StudentAssessment.Status.DRAFT:
        raise ValidationError(
            f"Cannot submit: current status is '{assessment.status}'. "
            f"Only DRAFT assessments can be submitted."
        )

    score_count = assessment.scores.filter(is_deleted=False).count()
    if score_count == 0:
        raise ValidationError(
            "Cannot submit assessment with no scores."
        )

    old_status = assessment.status
    assessment.status = StudentAssessment.Status.SUBMITTED
    assessment.submitted_by = submitted_by
    assessment.save()

    audit_log(
        action="UPDATE",
        instance=assessment,
        old_data={"status": old_status},
        new_data={"status": assessment.status, "submitted_by": str(submitted_by.pk)},
        user=submitted_by,
    )

    logger.info(
        f"Assessment submitted: {assessment.pk} "
        f"by={submitted_by.email}"
    )

    return assessment


@transaction.atomic
def approve_assessment(*, assessment_id, approved_by):
    """
    Transition SUBMITTED → APPROVED.

    Args:
        assessment_id: UUID
        approved_by: User performing the action

    Returns:
        Updated StudentAssessment instance

    Raises:
        ValidationError on invalid transition
    """
    assessment = StudentAssessment.objects.select_for_update().get(
        pk=assessment_id, is_deleted=False,
    )

    if assessment.status != StudentAssessment.Status.SUBMITTED:
        raise ValidationError(
            f"Cannot approve: current status is '{assessment.status}'. "
            f"Only SUBMITTED assessments can be approved."
        )

    old_status = assessment.status
    assessment.status = StudentAssessment.Status.APPROVED
    assessment.approved_by = approved_by
    assessment.save()

    audit_log(
        action="UPDATE",
        instance=assessment,
        old_data={"status": old_status},
        new_data={"status": assessment.status, "approved_by": str(approved_by.pk)},
        user=approved_by,
    )

    logger.info(
        f"Assessment approved: {assessment.pk} "
        f"by={approved_by.email}"
    )

    return assessment


def get_quarterly_summary(*, student_id, quarter_id):
    """
    Generate aggregated summary of all assessments for a student in a quarter.

    Returns:
        list of dicts with assessment_type_name, total_score, total_max, percentage
    """
    assessments = StudentAssessment.objects.filter(
        student_id=student_id,
        quarter_id=quarter_id,
        is_deleted=False,
    ).select_related("assessment_type")

    results = []
    for asmt in assessments:
        scores = StudentAssessmentScore.objects.filter(
            student_assessment=asmt,
            is_deleted=False,
        ).select_related("criteria")

        total_score = sum(s.score for s in scores)
        total_max = sum(s.criteria.max_score for s in scores)
        pct = (
            Decimal(total_score) / Decimal(total_max) * 100
            if total_max > 0
            else Decimal("0")
        )

        results.append({
            "assessment_type_name": asmt.assessment_type.name,
            "total_score": total_score,
            "total_max_score": total_max,
            "percentage": round(pct, 2),
            "status": asmt.status,
            "score_count": scores.count() if hasattr(scores, 'count') else len(scores),
        })

    return results
