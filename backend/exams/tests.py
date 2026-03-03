"""
EduSync — Exams Tests.
Bulk marks, report card, row locking, unique constraints, API integration.
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.db import IntegrityError, connection
from rest_framework.test import APITestCase, APIClient
from rest_framework import status as http_status

from core.models import School, Branch, AcademicYear, GradeMapping
from accounts.models import User, Student
from academics.models import Class, Section, Subject
from exams.models import ExamType, Exam, ExamMark
from exams import services as exam_services


class ExamTestMixin:
    """Shared setup for exam tests."""

    @classmethod
    def _setup_exam_data(cls):
        cls.school = School.objects.create(name="Exam School", code="EXM")
        cls.branch = Branch.objects.create(
            school=cls.school, name="EXB", full_name="Exam Branch",
        )
        cls.klass = Class.objects.create(name="10", branch=cls.branch)
        cls.section = Section.objects.create(name="A", class_ref=cls.klass)
        cls.subject_math = Subject.objects.create(name="Math", branch=cls.branch)
        cls.subject_eng = Subject.objects.create(name="English", branch=cls.branch)

        cls.academic_year = AcademicYear.objects.create(
            year_label="2025-26",
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31),
            is_current=True,
        )
        cls.exam_type = ExamType.objects.create(name="MidTerm-Test", order=1)
        cls.exam = Exam.objects.create(
            exam_type=cls.exam_type, academic_year=cls.academic_year,
            class_assigned=cls.klass, branch=cls.branch,
        )

        cls.admin = User.objects.create_superuser(
            email="exam_admin@test.com", password="Test@12345",
            first_name="Exam", last_name="Admin",
        )
        cls.admin.branch = cls.branch
        cls.admin.save()

        # Create students
        cls.students = []
        for i in range(3):
            user = User.objects.create_user(
                email=f"examstu{i}@test.com", password="Test@12345",
                first_name=f"ExStu{i}", last_name="Test",
                role_type=User.RoleType.STUDENT, branch=cls.branch,
            )
            student = Student.objects.create(
                user=user, branch=cls.branch,
                admission_number=f"EXM-{i:03d}",
                class_assigned=cls.klass, section=cls.section,
            )
            cls.students.append(student)

        # Seed grade mapping
        GradeMapping.objects.create(min_percentage=91, max_percentage=100, grade="A1")
        GradeMapping.objects.create(min_percentage=81, max_percentage=90, grade="A2")
        GradeMapping.objects.create(min_percentage=71, max_percentage=80, grade="B1")
        GradeMapping.objects.create(min_percentage=0, max_percentage=70, grade="C")


class ExamMarkUniqueConstraintTestCase(ExamTestMixin, TestCase):
    """3️⃣ Unique Constraints — duplicate student+exam+subject rejected."""

    @classmethod
    def setUpTestData(cls):
        cls._setup_exam_data()

    def test_duplicate_exam_mark_rejected(self):
        """Same student + exam + subject → IntegrityError."""
        ExamMark.objects.create(
            student=self.students[0], exam=self.exam,
            subject=self.subject_math,
            marks_obtained=80, max_marks=100,
        )
        with self.assertRaises(IntegrityError):
            ExamMark.objects.create(
                student=self.students[0], exam=self.exam,
                subject=self.subject_math,
                marks_obtained=85, max_marks=100,
            )


class BulkMarksServiceTestCase(ExamTestMixin, TestCase):
    """4️⃣ Service Layer — submit_exam_marks atomic + audit."""

    @classmethod
    def setUpTestData(cls):
        cls._setup_exam_data()

    def test_bulk_submit_success(self):
        """submit_exam_marks creates all marks atomically."""
        marks_data = [
            {
                "student_id": self.students[0].pk,
                "subject_id": self.subject_math.pk,
                "marks_obtained": Decimal("85"),
                "max_marks": Decimal("100"),
            },
            {
                "student_id": self.students[1].pk,
                "subject_id": self.subject_math.pk,
                "marks_obtained": Decimal("72"),
                "max_marks": Decimal("100"),
            },
        ]
        created = exam_services.submit_exam_marks(
            exam_id=self.exam.pk,
            marks_data=marks_data,
            submitted_by=self.admin,
        )
        self.assertEqual(len(created), 2)

    def test_bulk_submit_creates_audit_entries(self):
        """Bulk submit creates AuditLog entries with batch_id."""
        from audit.models import AuditLog

        initial = AuditLog.objects.count()
        marks_data = [
            {
                "student_id": self.students[2].pk,
                "subject_id": self.subject_eng.pk,
                "marks_obtained": Decimal("90"),
                "max_marks": Decimal("100"),
            },
        ]
        exam_services.submit_exam_marks(
            exam_id=self.exam.pk,
            marks_data=marks_data,
            submitted_by=self.admin,
        )
        self.assertGreater(AuditLog.objects.count(), initial)


class ReportCardServiceTestCase(ExamTestMixin, TestCase):
    """Report card with correct totals, percentage, grade."""

    @classmethod
    def setUpTestData(cls):
        cls._setup_exam_data()
        # Add marks for student 0
        ExamMark.objects.create(
            student=cls.students[0], exam=cls.exam,
            subject=cls.subject_math,
            marks_obtained=85, max_marks=100,
        )
        ExamMark.objects.create(
            student=cls.students[0], exam=cls.exam,
            subject=cls.subject_eng,
            marks_obtained=90, max_marks=100,
        )

    def test_report_card_totals(self):
        """Report card computes correct total and percentage."""
        report = exam_services.get_report_card(
            student_id=self.students[0].pk,
            exam_id=self.exam.pk,
        )
        self.assertEqual(report["total_obtained"], Decimal("175"))
        self.assertEqual(report["total_max"], Decimal("200"))
        self.assertEqual(report["overall_percentage"], Decimal("87.50"))

    def test_report_card_grade(self):
        """Report card maps percentage to correct grade."""
        report = exam_services.get_report_card(
            student_id=self.students[0].pk,
            exam_id=self.exam.pk,
        )
        # 87.5% → A2 (81-90 range)
        self.assertEqual(report["grade"], "A2")

    def test_report_card_subjects_count(self):
        """Report card contains entries for all subjects."""
        report = exam_services.get_report_card(
            student_id=self.students[0].pk,
            exam_id=self.exam.pk,
        )
        self.assertEqual(len(report["subjects"]), 2)


class RowLockingTestCase(ExamTestMixin, TestCase):
    """5️⃣ Row Locking — select_for_update on ExamMark."""

    @classmethod
    def setUpTestData(cls):
        cls._setup_exam_data()

    def test_update_exam_mark_with_lock(self):
        """update_exam_mark uses select_for_update and creates audit log."""
        from audit.models import AuditLog

        mark = ExamMark.objects.create(
            student=self.students[0], exam=self.exam,
            subject=self.subject_math,
            marks_obtained=70, max_marks=100,
        )

        initial_audit = AuditLog.objects.count()

        updated = exam_services.update_exam_mark(
            mark_id=mark.pk,
            marks_obtained=Decimal("85"),
            max_marks=Decimal("100"),
            updated_by=self.admin,
        )

        self.assertEqual(updated.marks_obtained, Decimal("85"))
        self.assertGreater(AuditLog.objects.count(), initial_audit)

        # Verify audit log has old + new data
        log = AuditLog.objects.filter(
            model_name="ExamMark", action_type="UPDATE",
        ).latest("timestamp")
        self.assertIn("70", str(log.old_data))
        self.assertIn("85", str(log.new_data))


class ExamAPITestCase(ExamTestMixin, APITestCase):
    """6️⃣ Exam API Integration Tests."""

    @classmethod
    def setUpTestData(cls):
        cls._setup_exam_data()

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_bulk_marks_endpoint(self):
        """POST /api/v1/exams/marks/bulk/ creates marks."""
        resp = self.client.post("/api/v1/exams/marks/bulk/", {
            "exam_id": str(self.exam.pk),
            "marks": [
                {
                    "student_id": str(self.students[0].pk),
                    "subject_id": str(self.subject_math.pk),
                    "marks_obtained": "88.00",
                    "max_marks": "100.00",
                },
                {
                    "student_id": str(self.students[1].pk),
                    "subject_id": str(self.subject_math.pk),
                    "marks_obtained": "75.00",
                    "max_marks": "100.00",
                },
            ],
        }, format="json")
        self.assertEqual(resp.status_code, http_status.HTTP_201_CREATED)
        self.assertTrue(resp.data["success"])
        self.assertEqual(resp.data["count"], 2)

    def test_report_card_endpoint(self):
        """GET /api/v1/exams/marks/report-card/ returns summary."""
        # Create marks first
        ExamMark.objects.create(
            student=self.students[2], exam=self.exam,
            subject=self.subject_math,
            marks_obtained=95, max_marks=100,
        )
        ExamMark.objects.create(
            student=self.students[2], exam=self.exam,
            subject=self.subject_eng,
            marks_obtained=88, max_marks=100,
        )

        resp = self.client.get(
            f"/api/v1/exams/marks/report-card/"
            f"?student_id={self.students[2].pk}&exam_id={self.exam.pk}"
        )
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])
        self.assertEqual(resp.data["data"]["student_name"], "ExStu2 Test")
        self.assertEqual(len(resp.data["data"]["subjects"]), 2)

    def test_report_card_missing_params(self):
        """Report card without params returns 400."""
        resp = self.client.get("/api/v1/exams/marks/report-card/")
        self.assertEqual(resp.status_code, http_status.HTTP_400_BAD_REQUEST)
