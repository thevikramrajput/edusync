"""
EduSync — Core App Tests.
Seeder idempotency, AcademicYear constraints.
"""
from io import StringIO
from django.test import TestCase
from django.core.management import call_command

from core.models import School, Branch, AcademicYear, GradeMapping
from accounts.models import Role
from exams.models import ExamType
from irregularities.models import IrregularityType


class SeederIdempotencyTestCase(TestCase):
    """7️⃣ Seeder Idempotency — 1 test"""

    def test_seed_initial_data_idempotent(self):
        """Running seed_initial_data twice produces no duplicates."""
        out1 = StringIO()
        call_command("seed_initial_data", stdout=out1)

        counts_after_first = {
            "schools": School.objects.count(),
            "branches": Branch.objects.count(),
            "roles": Role.objects.count(),
            "exam_types": ExamType.objects.count(),
            "irregularity_types": IrregularityType.objects.count(),
            "grade_mappings": GradeMapping.objects.count(),
        }

        out2 = StringIO()
        call_command("seed_initial_data", stdout=out2)

        counts_after_second = {
            "schools": School.objects.count(),
            "branches": Branch.objects.count(),
            "roles": Role.objects.count(),
            "exam_types": ExamType.objects.count(),
            "irregularity_types": IrregularityType.objects.count(),
            "grade_mappings": GradeMapping.objects.count(),
        }

        self.assertEqual(counts_after_first, counts_after_second)
        # Verify second run says "Exists"
        self.assertIn("Exists", out2.getvalue())


class AcademicYearTestCase(TestCase):
    """Model-level: AcademicYear single-current enforcement."""

    def test_only_one_current_academic_year(self):
        """Setting a new year as current unsets the previous one."""
        from datetime import date

        yr1 = AcademicYear.objects.create(
            year_label="2024-25",
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31),
            is_current=True,
        )
        yr2 = AcademicYear.objects.create(
            year_label="2025-26",
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31),
            is_current=True,
        )

        yr1.refresh_from_db()
        self.assertFalse(yr1.is_current)
        self.assertTrue(yr2.is_current)
