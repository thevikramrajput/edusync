"""
EduSync — Common Infrastructure Tests.
Soft delete behavior, branch isolation, audit logging.
"""
from django.test import TestCase
from django.db import IntegrityError

from core.models import School, Branch, AcademicYear
from accounts.models import User, Student, Faculty
from academics.models import Class, Section
from audit.models import AuditLog
from common.services import audit_log, audit_bulk_create, audit_queryset_update, set_current_user


class SoftDeleteTestCase(TestCase):
    """1️⃣ Soft Delete Behavior — 4 tests"""

    @classmethod
    def setUpTestData(cls):
        cls.school = School.objects.create(name="Test School", code="TST")
        cls.branch = Branch.objects.create(
            school=cls.school, name="BR1", full_name="Branch One",
        )
        cls.klass = Class.objects.create(name="10", branch=cls.branch)
        cls.section = Section.objects.create(name="A", class_ref=cls.klass)

    def _create_student(self, email, admission):
        user = User.objects.create_user(
            email=email, password="Test@12345",
            first_name="Test", last_name="Student",
            role_type=User.RoleType.STUDENT, branch=self.branch,
        )
        return Student.objects.create(
            user=user, branch=self.branch,
            admission_number=admission,
            class_assigned=self.klass, section=self.section,
        )

    def test_soft_delete_sets_is_deleted(self):
        """delete() on BaseModel sets is_deleted=True, not physical delete."""
        student = self._create_student("sd1@test.com", "SD-001")
        student.delete()
        student.refresh_from_db()
        self.assertTrue(student.is_deleted)

    def test_default_manager_excludes_deleted(self):
        """objects manager excludes soft-deleted records."""
        student = self._create_student("sd2@test.com", "SD-002")
        student.delete()
        self.assertFalse(Student.objects.filter(pk=student.pk).exists())

    def test_all_objects_includes_deleted(self):
        """all_objects manager includes soft-deleted records."""
        student = self._create_student("sd3@test.com", "SD-003")
        student.delete()
        self.assertTrue(Student.all_objects.filter(pk=student.pk).exists())

    def test_recreate_after_soft_delete(self):
        """
        Partial unique constraint: create → soft delete → recreate
        with same admission_number MUST succeed.
        """
        student = self._create_student("sd4@test.com", "SD-004")
        student.delete()  # Soft delete
        student.user.is_deleted = True
        student.user.save()

        # Recreate with same admission_number in same branch
        new_student = self._create_student("sd4b@test.com", "SD-004")
        self.assertEqual(new_student.admission_number, "SD-004")
        self.assertFalse(new_student.is_deleted)


class BranchIsolationTestCase(TestCase):
    """2️⃣ Branch Isolation — 3 tests"""

    @classmethod
    def setUpTestData(cls):
        cls.school = School.objects.create(name="Test School", code="ISO")
        cls.branch_a = Branch.objects.create(
            school=cls.school, name="BRA", full_name="Branch A",
        )
        cls.branch_b = Branch.objects.create(
            school=cls.school, name="BRB", full_name="Branch B",
        )
        cls.klass_a = Class.objects.create(name="10", branch=cls.branch_a)
        cls.klass_b = Class.objects.create(name="10", branch=cls.branch_b)
        cls.section_a = Section.objects.create(name="A", class_ref=cls.klass_a)
        cls.section_b = Section.objects.create(name="A", class_ref=cls.klass_b)

        # Create students in each branch
        for i in range(3):
            user = User.objects.create_user(
                email=f"bra{i}@test.com", password="Test@12345",
                first_name=f"BrA{i}", last_name="Student",
                role_type=User.RoleType.STUDENT, branch=cls.branch_a,
            )
            Student.objects.create(
                user=user, branch=cls.branch_a,
                admission_number=f"BRA-{i:03d}",
                class_assigned=cls.klass_a, section=cls.section_a,
            )
        for i in range(2):
            user = User.objects.create_user(
                email=f"brb{i}@test.com", password="Test@12345",
                first_name=f"BrB{i}", last_name="Student",
                role_type=User.RoleType.STUDENT, branch=cls.branch_b,
            )
            Student.objects.create(
                user=user, branch=cls.branch_b,
                admission_number=f"BRB-{i:03d}",
                class_assigned=cls.klass_b, section=cls.section_b,
            )

    def test_for_branch_filters_correctly(self):
        """for_branch() returns only students in the specified branch."""
        students_a = Student.objects.for_branch(self.branch_a.pk)
        self.assertEqual(students_a.count(), 3)
        for s in students_a:
            self.assertEqual(s.branch_id, self.branch_a.pk)

    def test_for_branch_excludes_other_branch(self):
        """Branch A query does not return Branch B students."""
        students_a = Student.objects.for_branch(self.branch_a.pk)
        student_branches = set(students_a.values_list("branch_id", flat=True))
        self.assertNotIn(self.branch_b.pk, student_branches)

    def test_global_scope_sees_all(self):
        """for_branch(None) returns all students across branches (GLOBAL)."""
        all_students = Student.objects.for_branch(None)
        self.assertEqual(all_students.count(), 5)


class AuditLoggingTestCase(TestCase):
    """4️⃣ Service Layer Audit Logging — 3 tests"""

    @classmethod
    def setUpTestData(cls):
        cls.school = School.objects.create(name="Audit School", code="AUD")
        cls.branch = Branch.objects.create(
            school=cls.school, name="AUB", full_name="Audit Branch",
        )
        cls.admin = User.objects.create_superuser(
            email="auditor@test.com", password="Test@12345",
            first_name="Audit", last_name="Admin",
        )

    def test_audit_log_creates_entry(self):
        """audit_log() creates an AuditLog record."""
        audit_log(
            action="CREATE",
            instance=self.branch,
            new_data={"name": self.branch.name},
            user=self.admin,
        )
        log = AuditLog.objects.filter(
            model_name="Branch", action_type="CREATE",
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.admin)

    def test_audit_bulk_create_with_batch_id(self):
        """audit_bulk_create creates entries with shared batch_id."""
        from exams.models import ExamType
        types = [
            ExamType(name="BulkTest1", order=100),
            ExamType(name="BulkTest2", order=101),
        ]
        created = audit_bulk_create(ExamType, types, user=self.admin)
        self.assertEqual(len(created), 2)

        logs = AuditLog.objects.filter(model_name="ExamType", action_type="CREATE")
        batch_ids = set(logs.values_list("batch_id", flat=True))
        # All entries share the same batch_id
        self.assertEqual(len(batch_ids), 1)
        self.assertIsNotNone(list(batch_ids)[0])

    def test_audit_queryset_update_snapshots(self):
        """audit_queryset_update captures old data before update."""
        branch2 = Branch.objects.create(
            school=self.school, name="AUC", full_name="Old Name",
        )
        qs = Branch.objects.filter(pk=branch2.pk)
        count = audit_queryset_update(qs, user=self.admin, full_name="New Name")
        self.assertEqual(count, 1)

        log = AuditLog.objects.filter(
            model_name="Branch", action_type="UPDATE",
        ).first()
        self.assertIsNotNone(log)
        self.assertIn("Old Name", str(log.old_data))
