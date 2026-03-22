"""
EduSync — Assessments Tests.
Status transitions, unique constraints, score validation,
branch isolation, atomic rollback, API integration.
"""
from datetime import date

from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status as http_status

from core.models import School, Branch, AcademicYear, Quarter
from accounts.models import User, Student
from academics.models import Class, Section
from assessments.models import (
    AssessmentType,
    AssessmentArea,
    AssessmentSubArea,
    AssessmentCriteria,
    StudentAssessment,
    StudentAssessmentScore,
)
from assessments import services as assessment_services


class AssessmentTestMixin:
    """Shared setup for assessment tests."""

    @classmethod
    def _setup_assessment_data(cls):
        cls.school = School.objects.create(name="Assmt School", code="ASM")
        cls.branch = Branch.objects.create(
            school=cls.school, name="ASB", full_name="Assmt Branch",
        )
        cls.branch_b = Branch.objects.create(
            school=cls.school, name="ASB2", full_name="Assmt Branch B",
        )
        cls.klass = Class.objects.create(name="10", branch=cls.branch)
        cls.section = Section.objects.create(name="A", class_ref=cls.klass)

        cls.academic_year = AcademicYear.objects.create(
            year_label="2025-26A",
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31),
            is_current=True,
        )
        cls.quarter = Quarter.objects.create(
            academic_year=cls.academic_year, name="Q1",
            start_date=date(2025, 4, 1), end_date=date(2025, 6, 30),
        )

        cls.admin = User.objects.create_superuser(
            email="assmt_admin@test.com", password="Test@12345",
            first_name="Assmt", last_name="Admin",
        )
        cls.admin.branch = cls.branch
        cls.admin.save()

        # Student
        user = User.objects.create_user(
            email="assmt_stu@test.com", password="Test@12345",
            first_name="Assmt", last_name="Student",
            role_type=User.RoleType.STUDENT, branch=cls.branch,
        )
        cls.student = Student.objects.create(
            user=user, branch=cls.branch,
            admission_number="ASM-001",
            class_assigned=cls.klass, section=cls.section,
        )

        # Assessment hierarchy: Type → Area → SubArea → Criteria
        cls.assessment_type = AssessmentType.objects.create(
            name="TestSocialEmotional", description="Test SE",
        )
        cls.area = AssessmentArea.objects.create(
            assessment_type=cls.assessment_type, name="Respectfulness", order=1,
        )
        cls.sub_area = AssessmentSubArea.objects.create(
            area=cls.area, name="Politeness", order=1,
        )
        cls.criteria1 = AssessmentCriteria.objects.create(
            sub_area=cls.sub_area, description="Greets teachers",
            max_score=5, order=1,
        )
        cls.criteria2 = AssessmentCriteria.objects.create(
            sub_area=cls.sub_area, description="Uses polite language",
            max_score=5, order=2,
        )


class StatusTransitionTestCase(AssessmentTestMixin, TestCase):
    """Status transition tests: DRAFT→SUBMITTED→APPROVED."""

    @classmethod
    def setUpTestData(cls):
        cls._setup_assessment_data()

    def _create_draft(self):
        return assessment_services.create_student_assessment(
            validated_data={
                "student": self.student,
                "academic_year": self.academic_year,
                "quarter": self.quarter,
                "assessment_type": self.assessment_type,
                "scores": [
                    {"criteria_id": self.criteria1.pk, "score": 4},
                    {"criteria_id": self.criteria2.pk, "score": 3},
                ],
            },
            branch=self.branch,
            created_by=self.admin,
        )

    def test_create_starts_as_draft(self):
        """Newly created assessment starts in DRAFT status."""
        assessment = self._create_draft()
        self.assertEqual(assessment.status, StudentAssessment.Status.DRAFT)

    def test_submit_transitions_to_submitted(self):
        """Submit changes DRAFT → SUBMITTED."""
        assessment = self._create_draft()
        submitted = assessment_services.submit_assessment(
            assessment_id=assessment.pk,
            submitted_by=self.admin,
        )
        self.assertEqual(submitted.status, StudentAssessment.Status.SUBMITTED)
        self.assertEqual(submitted.submitted_by, self.admin)

    def test_approve_transitions_to_approved(self):
        """Approve changes SUBMITTED → APPROVED."""
        assessment = self._create_draft()
        assessment_services.submit_assessment(
            assessment_id=assessment.pk,
            submitted_by=self.admin,
        )
        approved = assessment_services.approve_assessment(
            assessment_id=assessment.pk,
            approved_by=self.admin,
        )
        self.assertEqual(approved.status, StudentAssessment.Status.APPROVED)
        self.assertEqual(approved.approved_by, self.admin)

    def test_cannot_submit_approved(self):
        """Cannot submit an already APPROVED assessment."""
        assessment = self._create_draft()
        assessment_services.submit_assessment(
            assessment_id=assessment.pk,
            submitted_by=self.admin,
        )
        assessment_services.approve_assessment(
            assessment_id=assessment.pk,
            approved_by=self.admin,
        )
        with self.assertRaises(ValidationError):
            assessment_services.submit_assessment(
                assessment_id=assessment.pk,
                submitted_by=self.admin,
            )

    def test_cannot_approve_draft(self):
        """Cannot approve a DRAFT assessment (must be SUBMITTED first)."""
        assessment = self._create_draft()
        with self.assertRaises(ValidationError):
            assessment_services.approve_assessment(
                assessment_id=assessment.pk,
                approved_by=self.admin,
            )

    def test_cannot_submit_without_scores(self):
        """Cannot submit assessment with 0 scores."""
        assessment = assessment_services.create_student_assessment(
            validated_data={
                "student": self.student,
                "academic_year": self.academic_year,
                "quarter": self.quarter,
                "assessment_type": self.assessment_type,
            },
            branch=self.branch,
            created_by=self.admin,
        )
        with self.assertRaises(ValidationError):
            assessment_services.submit_assessment(
                assessment_id=assessment.pk,
                submitted_by=self.admin,
            )


class UniqueConstraintTestCase(AssessmentTestMixin, TestCase):
    """Unique (student, quarter, assessment_type) constraint."""

    @classmethod
    def setUpTestData(cls):
        cls._setup_assessment_data()

    def test_duplicate_student_quarter_type_rejected(self):
        """Same student + quarter + type → IntegrityError."""
        assessment_services.create_student_assessment(
            validated_data={
                "student": self.student,
                "academic_year": self.academic_year,
                "quarter": self.quarter,
                "assessment_type": self.assessment_type,
            },
            branch=self.branch,
            created_by=self.admin,
        )
        with self.assertRaises(IntegrityError):
            assessment_services.create_student_assessment(
                validated_data={
                    "student": self.student,
                    "academic_year": self.academic_year,
                    "quarter": self.quarter,
                    "assessment_type": self.assessment_type,
                },
                branch=self.branch,
                created_by=self.admin,
            )


class ScoreValidationTestCase(AssessmentTestMixin, TestCase):
    """Score max_score validation."""

    @classmethod
    def setUpTestData(cls):
        cls._setup_assessment_data()

    def test_score_exceeding_max_raises(self):
        """Score > criteria.max_score raises ValidationError."""
        with self.assertRaises(ValidationError):
            assessment_services.create_student_assessment(
                validated_data={
                    "student": self.student,
                    "academic_year": self.academic_year,
                    "quarter": self.quarter,
                    "assessment_type": self.assessment_type,
                    "scores": [
                        {"criteria_id": self.criteria1.pk, "score": 10},  # max=5
                    ],
                },
                branch=self.branch,
                created_by=self.admin,
            )

    def test_valid_scores_accepted(self):
        """Score <= max_score is accepted."""
        assessment = assessment_services.create_student_assessment(
            validated_data={
                "student": self.student,
                "academic_year": self.academic_year,
                "quarter": self.quarter,
                "assessment_type": self.assessment_type,
                "scores": [
                    {"criteria_id": self.criteria1.pk, "score": 5},  # max=5
                    {"criteria_id": self.criteria2.pk, "score": 0},
                ],
            },
            branch=self.branch,
            created_by=self.admin,
        )
        self.assertEqual(assessment.scores.count(), 2)

    def test_score_rollback_on_invalid(self):
        """Atomic rollback: no assessment created if score validation fails."""
        initial_count = StudentAssessment.objects.count()
        try:
            assessment_services.create_student_assessment(
                validated_data={
                    "student": self.student,
                    "academic_year": self.academic_year,
                    "quarter": self.quarter,
                    "assessment_type": self.assessment_type,
                    "scores": [
                        {"criteria_id": self.criteria1.pk, "score": 99},
                    ],
                },
                branch=self.branch,
                created_by=self.admin,
            )
        except ValidationError:
            pass
        self.assertEqual(StudentAssessment.objects.count(), initial_count)


class BranchIsolationTestCase(AssessmentTestMixin, TestCase):
    """Assessments respect branch isolation."""

    @classmethod
    def setUpTestData(cls):
        cls._setup_assessment_data()

    def test_assessments_filtered_by_branch(self):
        """for_branch returns only assessments in the specified branch."""
        assessment_services.create_student_assessment(
            validated_data={
                "student": self.student,
                "academic_year": self.academic_year,
                "quarter": self.quarter,
                "assessment_type": self.assessment_type,
            },
            branch=self.branch,
            created_by=self.admin,
        )
        # Branch A sees assessments
        qs_a = StudentAssessment.objects.for_branch(self.branch.pk)
        self.assertEqual(qs_a.count(), 1)

        # Branch B sees nothing
        qs_b = StudentAssessment.objects.for_branch(self.branch_b.pk)
        self.assertEqual(qs_b.count(), 0)


class AssessmentAPITestCase(AssessmentTestMixin, APITestCase):
    """API integration tests for assessments."""

    @classmethod
    def setUpTestData(cls):
        cls._setup_assessment_data()

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_create_assessment_via_api(self):
        """POST /api/v1/assessments/student/ creates assessment with scores."""
        resp = self.client.post("/api/v1/assessments/student/", {
            "student": str(self.student.pk),
            "academic_year": str(self.academic_year.pk),
            "quarter": str(self.quarter.pk),
            "assessment_type": str(self.assessment_type.pk),
            "scores": [
                {"criteria_id": str(self.criteria1.pk), "score": 4},
                {"criteria_id": str(self.criteria2.pk), "score": 3},
            ],
        }, format="json")
        self.assertEqual(resp.status_code, http_status.HTTP_201_CREATED)
        self.assertTrue(resp.data["success"])
        self.assertEqual(resp.data["data"]["status"], "DRAFT")

    def test_submit_via_api(self):
        """POST /api/v1/assessments/student/{id}/submit/ transitions to SUBMITTED."""
        assessment = assessment_services.create_student_assessment(
            validated_data={
                "student": self.student,
                "academic_year": self.academic_year,
                "quarter": self.quarter,
                "assessment_type": self.assessment_type,
                "scores": [
                    {"criteria_id": self.criteria1.pk, "score": 4},
                ],
            },
            branch=self.branch,
            created_by=self.admin,
        )
        resp = self.client.post(f"/api/v1/assessments/student/{assessment.pk}/submit/")
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])
        self.assertEqual(resp.data["data"]["status"], "SUBMITTED")

    def test_approve_via_api(self):
        """POST /api/v1/assessments/student/{id}/approve/ transitions to APPROVED."""
        assessment = assessment_services.create_student_assessment(
            validated_data={
                "student": self.student,
                "academic_year": self.academic_year,
                "quarter": self.quarter,
                "assessment_type": self.assessment_type,
                "scores": [
                    {"criteria_id": self.criteria1.pk, "score": 4},
                ],
            },
            branch=self.branch,
            created_by=self.admin,
        )
        assessment_services.submit_assessment(
            assessment_id=assessment.pk,
            submitted_by=self.admin,
        )
        resp = self.client.post(f"/api/v1/assessments/student/{assessment.pk}/approve/")
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])
        self.assertEqual(resp.data["data"]["status"], "APPROVED")

    def test_quarterly_summary_via_api(self):
        """GET /api/v1/assessments/student/quarterly-summary/ returns aggregation."""
        assessment = assessment_services.create_student_assessment(
            validated_data={
                "student": self.student,
                "academic_year": self.academic_year,
                "quarter": self.quarter,
                "assessment_type": self.assessment_type,
                "scores": [
                    {"criteria_id": self.criteria1.pk, "score": 4},
                    {"criteria_id": self.criteria2.pk, "score": 3},
                ],
            },
            branch=self.branch,
            created_by=self.admin,
        )
        resp = self.client.get(
            f"/api/v1/assessments/student/quarterly-summary/"
            f"?student_id={self.student.pk}&quarter_id={self.quarter.pk}"
        )
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])
        self.assertEqual(len(resp.data["data"]), 1)
        summary = resp.data["data"][0]
        self.assertEqual(summary["total_score"], 7)
        self.assertEqual(summary["total_max_score"], 10)
