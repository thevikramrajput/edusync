"""
EduSync — Exams Service Layer.
Atomic bulk mark submission with audit logging and row locking for updates.
"""
import logging
from decimal import Decimal

from django.db import transaction

from accounts.models import Student
from academics.models import Subject
from exams.models import Exam, ExamMark
from core.models import GradeMapping
from common.services import audit_log, audit_bulk_create

logger = logging.getLogger("edusync.audit")


@transaction.atomic
def submit_exam_marks(*, exam_id, marks_data, submitted_by=None):
    """
    Bulk create exam marks for a given exam.
    Atomic — all-or-nothing. Audit logged with batch_id.

    Args:
        exam_id: UUID of the exam
        marks_data: list of dicts [{student_id, subject_id, marks_obtained, max_marks}]
        submitted_by: User submitting the marks

    Returns:
        list of created ExamMark objects
    """
    exam = Exam.objects.select_for_update().get(pk=exam_id)

    # Validate all students and subjects exist
    student_ids = {m["student_id"] for m in marks_data}
    subject_ids = {m["subject_id"] for m in marks_data}

    students = {str(s.pk): s for s in Student.objects.filter(pk__in=student_ids, is_deleted=False)}
    subjects = {str(s.pk): s for s in Subject.objects.filter(pk__in=subject_ids, is_deleted=False)}

    if len(students) != len(student_ids):
        missing = student_ids - {s.pk for s in students.values()}
        raise ValueError(f"Students not found: {missing}")

    if len(subjects) != len(subject_ids):
        missing = subject_ids - {s.pk for s in subjects.values()}
        raise ValueError(f"Subjects not found: {missing}")

    mark_objects = [
        ExamMark(
            student=students[str(m["student_id"])],
            exam=exam,
            subject=subjects[str(m["subject_id"])],
            marks_obtained=m["marks_obtained"],
            max_marks=m["max_marks"],
        )
        for m in marks_data
    ]

    created = audit_bulk_create(ExamMark, mark_objects, user=submitted_by)

    logger.info(
        f"Bulk marks submitted: exam={exam.pk} count={len(created)} "
        f"by={getattr(submitted_by, 'email', 'system')}"
    )

    return created


@transaction.atomic
def update_exam_mark(*, mark_id, marks_obtained, max_marks, updated_by=None):
    """
    Update a single exam mark with row-level locking (select_for_update).

    Args:
        mark_id: UUID of the ExamMark
        marks_obtained: new marks
        max_marks: new max marks
        updated_by: User performing the update

    Returns:
        Updated ExamMark instance
    """
    mark = ExamMark.objects.select_for_update().get(pk=mark_id, is_deleted=False)

    old_data = {
        "marks_obtained": str(mark.marks_obtained),
        "max_marks": str(mark.max_marks),
    }

    mark.marks_obtained = marks_obtained
    mark.max_marks = max_marks
    mark.save()

    audit_log(
        action="UPDATE",
        instance=mark,
        old_data=old_data,
        new_data={
            "marks_obtained": str(marks_obtained),
            "max_marks": str(max_marks),
        },
        user=updated_by,
    )

    return mark


def get_report_card(*, student_id, exam_id):
    """
    Generate report card for a student + exam.
    Computes totals, percentage, and grade via Python (not annotation).

    Args:
        student_id: UUID
        exam_id: UUID

    Returns:
        dict with subjects, totals, percentage, and grade
    """
    student = Student.objects.select_related("user").get(pk=student_id, is_deleted=False)
    exam = Exam.objects.select_related("exam_type").get(pk=exam_id, is_deleted=False)

    marks = ExamMark.objects.filter(
        student=student, exam=exam, is_deleted=False,
    ).select_related("subject").order_by("subject__name")

    subjects = []
    total_obtained = Decimal("0")
    total_max = Decimal("0")

    for m in marks:
        pct = (m.marks_obtained / m.max_marks * 100) if m.max_marks > 0 else Decimal("0")
        subjects.append({
            "subject_name": m.subject.name,
            "marks_obtained": m.marks_obtained,
            "max_marks": m.max_marks,
            "percentage": round(pct, 2),
        })
        total_obtained += m.marks_obtained
        total_max += m.max_marks

    overall_pct = (total_obtained / total_max * 100) if total_max > 0 else Decimal("0")
    overall_pct = round(overall_pct, 2)

    # Grade mapping
    grade_obj = GradeMapping.objects.filter(
        min_percentage__lte=overall_pct,
        max_percentage__gte=overall_pct,
        is_deleted=False,
    ).first()
    grade = grade_obj.grade if grade_obj else "N/A"

    return {
        "student_name": student.user.full_name,
        "admission_number": student.admission_number,
        "exam_name": exam.exam_type.name,
        "subjects": subjects,
        "total_obtained": total_obtained,
        "total_max": total_max,
        "overall_percentage": overall_pct,
        "grade": grade,
    }
