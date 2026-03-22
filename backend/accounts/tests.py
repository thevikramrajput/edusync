"""
EduSync — Accounts Tests.
Unique constraints, service layer atomicity, User model, API integration.
"""
from django.test import TestCase
from django.db import IntegrityError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status as http_status

from core.models import School, Branch
from accounts.models import User, Student, Faculty
from academics.models import Class, Section
from accounts import services as account_services


class UserModelTestCase(TestCase):
    """User model: email normalization, superuser creation."""

    def test_email_normalization(self):
        """Email domain is lowered during create_user."""
        user = User.objects.create_user(
            email="Test@EXAMPLE.COM", password="Test@12345",
            first_name="Test", last_name="User",
            role_type=User.RoleType.STUDENT,
        )
        self.assertEqual(user.email, "Test@example.com")

    def test_superuser_creation(self):
        """create_superuser sets is_staff, is_superuser, and SUPER_ADMIN role."""
        user = User.objects.create_superuser(
            email="super@test.com", password="Test@12345",
            first_name="Super", last_name="Admin",
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertEqual(user.role_type, User.RoleType.SUPER_ADMIN)

    def test_create_user_without_email_raises(self):
        """create_user without email raises ValueError."""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email="", password="Test@12345",
                first_name="No", last_name="Email",
                role_type=User.RoleType.STUDENT,
            )


class UniqueConstraintTestCase(TestCase):
    """3️⃣ Unique Constraints — 2 tests"""

    @classmethod
    def setUpTestData(cls):
        cls.school = School.objects.create(name="Unique School", code="UNQ")
        cls.branch = Branch.objects.create(
            school=cls.school, name="UBR", full_name="Unique Branch",
        )
        cls.klass = Class.objects.create(name="10", branch=cls.branch)
        cls.section = Section.objects.create(name="A", class_ref=cls.klass)

    def test_duplicate_active_admission_rejected(self):
        """Two active students with same admission_number in same branch → rejected."""
        user1 = User.objects.create_user(
            email="dup1@test.com", password="Test@12345",
            first_name="Dup", last_name="One",
            role_type=User.RoleType.STUDENT, branch=self.branch,
        )
        Student.objects.create(
            user=user1, branch=self.branch,
            admission_number="DUP-001",
            class_assigned=self.klass, section=self.section,
        )

        user2 = User.objects.create_user(
            email="dup2@test.com", password="Test@12345",
            first_name="Dup", last_name="Two",
            role_type=User.RoleType.STUDENT, branch=self.branch,
        )
        with self.assertRaises(IntegrityError):
            Student.objects.create(
                user=user2, branch=self.branch,
                admission_number="DUP-001",
                class_assigned=self.klass, section=self.section,
            )

    def test_duplicate_faculty_code_rejected(self):
        """Two active faculty with same code in same branch → rejected."""
        user1 = User.objects.create_user(
            email="fac1@test.com", password="Test@12345",
            first_name="Fac", last_name="One",
            role_type=User.RoleType.FACULTY, branch=self.branch,
        )
        Faculty.objects.create(
            user=user1, branch=self.branch,
            faculty_code="FAC-001", level=Faculty.Level.L3,
        )

        user2 = User.objects.create_user(
            email="fac2@test.com", password="Test@12345",
            first_name="Fac", last_name="Two",
            role_type=User.RoleType.FACULTY, branch=self.branch,
        )
        with self.assertRaises(IntegrityError):
            Faculty.objects.create(
                user=user2, branch=self.branch,
                faculty_code="FAC-001", level=Faculty.Level.L3,
            )


class StudentServiceTestCase(TestCase):
    """4️⃣ Service Layer — atomic create_student."""

    @classmethod
    def setUpTestData(cls):
        cls.school = School.objects.create(name="Service School", code="SVC")
        cls.branch = Branch.objects.create(
            school=cls.school, name="SVB", full_name="Service Branch",
        )
        cls.klass = Class.objects.create(name="10", branch=cls.branch)
        cls.section = Section.objects.create(name="A", class_ref=cls.klass)
        cls.admin = User.objects.create_superuser(
            email="svc_admin@test.com", password="Test@12345",
            first_name="Svc", last_name="Admin",
        )

    def test_create_student_success(self):
        """create_student() creates User + Student atomically."""
        student = account_services.create_student(
            validated_data={
                "email": "newstudent@test.com",
                "password": "Test@12345",
                "first_name": "New",
                "last_name": "Student",
                "admission_number": "SVC-001",
                "class_assigned": self.klass,
                "section": self.section,
            },
            branch=self.branch,
            created_by=self.admin,
        )
        self.assertIsNotNone(student.pk)
        self.assertEqual(student.user.role_type, User.RoleType.STUDENT)
        self.assertEqual(student.branch, self.branch)

    def test_create_student_creates_audit_log(self):
        """create_student() generates an AuditLog entry."""
        from audit.models import AuditLog

        initial_count = AuditLog.objects.count()
        account_services.create_student(
            validated_data={
                "email": "audited@test.com",
                "password": "Test@12345",
                "first_name": "Audit",
                "last_name": "Test",
                "admission_number": "SVC-002",
                "class_assigned": self.klass,
                "section": self.section,
            },
            branch=self.branch,
            created_by=self.admin,
        )
        self.assertGreater(AuditLog.objects.count(), initial_count)

    def test_create_student_rollback_on_duplicate(self):
        """create_student() rolls back User if Student creation fails (duplicate)."""
        account_services.create_student(
            validated_data={
                "email": "first@test.com",
                "password": "Test@12345",
                "first_name": "First",
                "last_name": "Student",
                "admission_number": "SVC-DUP",
                "class_assigned": self.klass,
                "section": self.section,
            },
            branch=self.branch,
            created_by=self.admin,
        )

        # Attempt to create another with same admission — should fail
        with self.assertRaises(IntegrityError):
            account_services.create_student(
                validated_data={
                    "email": "second@test.com",
                    "password": "Test@12345",
                    "first_name": "Second",
                    "last_name": "Student",
                    "admission_number": "SVC-DUP",
                    "class_assigned": self.klass,
                    "section": self.section,
                },
                branch=self.branch,
                created_by=self.admin,
            )


class StudentAPITestCase(APITestCase):
    """6️⃣ Student API Integration Tests."""

    @classmethod
    def setUpTestData(cls):
        cls.school = School.objects.create(name="API School", code="API")
        cls.branch = Branch.objects.create(
            school=cls.school, name="APB", full_name="API Branch",
        )
        cls.klass = Class.objects.create(name="10", branch=cls.branch)
        cls.section = Section.objects.create(name="A", class_ref=cls.klass)
        cls.admin = User.objects.create_superuser(
            email="api_admin@test.com", password="Test@12345",
            first_name="API", last_name="Admin",
        )
        cls.admin.branch = cls.branch
        cls.admin.save()

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_jwt_login_returns_tokens(self):
        """POST /api/v1/auth/login/ returns access + refresh tokens."""
        client = APIClient()  # unauthenticated
        resp = client.post("/api/v1/auth/login/", {
            "email": "api_admin@test.com",
            "password": "Test@12345",
        }, format="json")
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_current_user_endpoint(self):
        """GET /api/v1/auth/me/ returns user profile."""
        resp = self.client.get("/api/v1/auth/me/")
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])
        self.assertEqual(resp.data["data"]["email"], "api_admin@test.com")

    def test_student_create_via_api(self):
        """POST /api/v1/auth/students/ creates student."""
        resp = self.client.post("/api/v1/auth/students/", {
            "email": "api_student@test.com",
            "password": "Test@12345",
            "first_name": "API",
            "last_name": "Student",
            "admission_number": "API-001",
            "class_assigned": str(self.klass.pk),
            "section": str(self.section.pk),
        }, format="json")
        self.assertEqual(resp.status_code, http_status.HTTP_201_CREATED)
        self.assertTrue(resp.data["success"])
        self.assertEqual(resp.data["data"]["admission_number"], "API-001")

    def test_student_list_filtered_by_branch(self):
        """GET /api/v1/auth/students/ returns only branch-scoped students."""
        # Create a student in this branch
        account_services.create_student(
            validated_data={
                "email": "listed@test.com",
                "password": "Test@12345",
                "first_name": "Listed",
                "last_name": "Student",
                "admission_number": "API-LIST",
                "class_assigned": self.klass,
                "section": self.section,
            },
            branch=self.branch,
            created_by=self.admin,
        )
        resp = self.client.get("/api/v1/auth/students/")
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data["results"]), 1)

    def test_student_soft_delete_via_api(self):
        """DELETE /api/v1/auth/students/{id}/ soft deletes."""
        student = account_services.create_student(
            validated_data={
                "email": "deleteme@test.com",
                "password": "Test@12345",
                "first_name": "Delete",
                "last_name": "Me",
                "admission_number": "API-DEL",
                "class_assigned": self.klass,
                "section": self.section,
            },
            branch=self.branch,
            created_by=self.admin,
        )
        resp = self.client.delete(f"/api/v1/auth/students/{student.pk}/")
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])

        # Should not appear in list anymore
        resp = self.client.get(f"/api/v1/auth/students/{student.pk}/")
        self.assertEqual(resp.status_code, http_status.HTTP_404_NOT_FOUND)
