"""
EduSync — Performance Baseline Test.
Seeds large dataset, measures query performance, detects N+1.
Run separately: docker compose exec web python manage.py test core.tests_performance -v2
"""
import time
from decimal import Decimal

from django.test import TestCase

from core.models import School, Branch, AcademicYear, GradeMapping
from accounts.models import User, Student
from academics.models import Class, Section, Subject
from exams.models import ExamType, Exam, ExamMark
from exams import services as exam_services


class PerformanceBaselineTestCase(TestCase):
    """
    Performance Baseline:
    - Seed 1 school, 3 branches, 5000 students, 30000 exam marks
    - Report card aggregation < 500ms
    - Detect N+1 via assertNumQueries
    """

    @classmethod
    def setUpTestData(cls):
        """Seed large dataset once for all performance tests."""
        cls.school = School.objects.create(name="Perf School", code="PRF")

        branches_data = [
            ("PB1", "Perf Branch 1"),
            ("PB2", "Perf Branch 2"),
            ("PB3", "Perf Branch 3"),
        ]
        cls.branches = []
        for name, full_name in branches_data:
            b = Branch.objects.create(school=cls.school, name=name, full_name=full_name)
            cls.branches.append(b)

        cls.academic_year = AcademicYear.objects.create(
            year_label="2025-26P",
            start_date="2025-04-01",
            end_date="2026-03-31",
            is_current=True,
        )

        # Grade mappings
        GradeMapping.objects.get_or_create(min_percentage=91, max_percentage=100, defaults={"grade": "A1"})
        GradeMapping.objects.get_or_create(min_percentage=81, max_percentage=90, defaults={"grade": "A2"})
        GradeMapping.objects.get_or_create(min_percentage=71, max_percentage=80, defaults={"grade": "B1"})
        GradeMapping.objects.get_or_create(min_percentage=61, max_percentage=70, defaults={"grade": "B2"})
        GradeMapping.objects.get_or_create(min_percentage=0, max_percentage=60, defaults={"grade": "C"})

        # 6 subjects
        cls.subjects = []
        for subj_name in ["Math", "English", "Science", "Hindi", "SST", "Computer"]:
            s = Subject.objects.create(name=f"Perf-{subj_name}", branch=cls.branches[0])
            cls.subjects.append(s)

        # Exam types and exams per branch
        cls.exam_type = ExamType.objects.create(name="PerfMidTerm", order=50)
        cls.exams = {}
        cls.classes = {}
        cls.sections = {}

        for branch in cls.branches:
            klass = Class.objects.create(name="10", branch=branch)
            section = Section.objects.create(name="A", class_ref=klass)
            cls.classes[branch.pk] = klass
            cls.sections[branch.pk] = section
            exam = Exam.objects.create(
                exam_type=cls.exam_type,
                academic_year=cls.academic_year,
                class_assigned=klass,
                branch=branch,
            )
            cls.exams[branch.pk] = exam

        # Seed 5000 students (split across branches)
        student_users = []
        students_per_branch = [2000, 1500, 1500]

        for b_idx, branch in enumerate(cls.branches):
            for i in range(students_per_branch[b_idx]):
                user = User(
                    email=f"perf_b{b_idx}_s{i}@test.com",
                    first_name=f"Perf{i}",
                    last_name=f"B{b_idx}",
                    role_type=User.RoleType.STUDENT,
                    branch=branch,
                )
                user.set_password("Test@12345")
                student_users.append(user)

        # Bulk create users
        User.objects.bulk_create(student_users, batch_size=500)

        # Retrieve created users and create students
        student_objects = []
        all_users = list(User.objects.filter(email__startswith="perf_"))
        for user in all_users:
            branch = user.branch
            student_objects.append(
                Student(
                    user=user,
                    branch=branch,
                    admission_number=f"PRF-{user.email.split('@')[0]}",
                    class_assigned=cls.classes[branch.pk],
                    section=cls.sections[branch.pk],
                )
            )

        Student.objects.bulk_create(student_objects, batch_size=500)
        cls.students = list(Student.objects.filter(branch__in=cls.branches))

        # Seed 30,000 exam marks (6 subjects × 5000 students)
        mark_objects = []
        for student in cls.students:
            exam = cls.exams[student.branch_id]
            for subj in cls.subjects:
                marks = Decimal(str(50 + (hash(str(student.pk) + str(subj.pk)) % 50)))
                mark_objects.append(
                    ExamMark(
                        student=student,
                        exam=exam,
                        subject=subj,
                        marks_obtained=marks,
                        max_marks=Decimal("100"),
                    )
                )

        ExamMark.objects.bulk_create(mark_objects, batch_size=1000)

    def test_student_count(self):
        """Verify 5000 students were seeded."""
        count = Student.objects.filter(branch__in=self.branches).count()
        self.assertEqual(count, 5000)

    def test_exam_marks_count(self):
        """Verify 30,000 marks were seeded."""
        count = ExamMark.objects.filter(exam__in=self.exams.values()).count()
        self.assertEqual(count, 30000)

    def test_report_card_performance(self):
        """Report card for one student completes in < 500ms."""
        student = self.students[0]
        exam = self.exams[student.branch_id]

        start = time.time()
        report = exam_services.get_report_card(
            student_id=student.pk,
            exam_id=exam.pk,
        )
        elapsed_ms = (time.time() - start) * 1000

        self.assertLess(elapsed_ms, 500, f"Report card took {elapsed_ms:.0f}ms (limit: 500ms)")
        self.assertEqual(len(report["subjects"]), 6)
        self.assertIsNotNone(report["grade"])

    def test_branch_filtered_query_performance(self):
        """Branch-filtered student list completes in < 200ms."""
        start = time.time()
        students = list(
            Student.objects.for_branch(self.branches[0].pk)
            .select_related("user", "branch", "class_assigned", "section")[:50]
        )
        elapsed_ms = (time.time() - start) * 1000

        self.assertLess(elapsed_ms, 200, f"Branch query took {elapsed_ms:.0f}ms (limit: 200ms)")
        self.assertEqual(len(students), 50)

    def test_report_card_no_n_plus_1(self):
        """Report card uses bounded queries, not N+1."""
        student = self.students[100]
        exam = self.exams[student.branch_id]

        # get_report_card should use at most:
        # 1 for student, 1 for exam, 1 for marks (with select_related), 1 for grade
        with self.assertNumQueries(4):
            exam_services.get_report_card(
                student_id=student.pk,
                exam_id=exam.pk,
            )
