"""
EduSync — Seed Initial Reference Data.
Idempotent — safe to run multiple times.
Usage: python manage.py seed_initial_data
"""
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Seed initial reference data (branches, roles, assessment types, etc.). Idempotent."

    @transaction.atomic
    def handle(self, *args, **options):
        self._seed_branches()
        self._seed_roles()
        self._seed_assessment_types()
        self._seed_exam_types()
        self._seed_irregularity_types()
        self._seed_grade_mapping()
        self.stdout.write(self.style.SUCCESS("✅ All initial data seeded successfully."))

    def _seed_branches(self):
        from core.models import School, Branch

        # Create default school
        school, created = School.objects.get_or_create(
            code="MKS",
            defaults={
                "name": "MKS Education",
            },
        )
        status = "Created" if created else "Exists"
        self.stdout.write(f"  School: MKS Education — {status}")

        branches = [
            ("CHK", "Chhuchhakwas", "CHK"),
            ("JJR", "Jhajjar", "JJR"),
            ("DADRI", "Charkhi Dadri", "DADRI"),
        ]
        for name, full_name, code in branches:
            obj, created = Branch.objects.get_or_create(
                name=name,
                defaults={"full_name": full_name, "code": code, "school": school},
            )
            status = "Created" if created else "Exists"
            self.stdout.write(f"  Branch: {name} — {status}")

    def _seed_roles(self):
        from accounts.models import Role

        roles = [
            ("DIRECTOR", "Director — oversees all branches"),
            ("PRINCIPAL", "Principal — heads a branch"),
            ("ACADEMIC_INCHARGE", "Academic Incharge — manages academics"),
            ("ACTIVITY_INCHARGE", "Activity Incharge — manages activities"),
            ("HOD", "Head of Department — subject head"),
            ("SECTION_INCHARGE", "Section Incharge — manages a class section"),
            ("SUBJECT_TEACHER", "Subject Teacher — teaches subjects"),
        ]
        for name, description in roles:
            obj, created = Role.objects.get_or_create(
                name=name,
                defaults={"description": description},
            )
            status = "Created" if created else "Exists"
            self.stdout.write(f"  Role: {name} — {status}")

    def _seed_assessment_types(self):
        from assessments.models import AssessmentType

        types = [
            ("SOCIAL_EMOTIONAL", "Social & Emotional Growth"),
            ("PHYSICAL_FITNESS", "Physical Growth & Fitness"),
            ("CO_CURRICULAR", "Co-Curricular Growth"),
            ("MIA_HABITS", "MIA Habits (Learning Growth)"),
        ]
        for name, description in types:
            obj, created = AssessmentType.objects.get_or_create(
                name=name,
                defaults={"description": description},
            )
            status = "Created" if created else "Exists"
            self.stdout.write(f"  AssessmentType: {name} — {status}")

    def _seed_exam_types(self):
        from exams.models import ExamType

        types = [
            ("MT-1", 1),
            ("PRE_MID", 2),
            ("MID_TERM", 3),
            ("MT-2", 4),
            ("POST_MID", 5),
            ("ANNUAL", 6),
        ]
        for name, order in types:
            obj, created = ExamType.objects.get_or_create(
                name=name,
                defaults={"order": order},
            )
            status = "Created" if created else "Exists"
            self.stdout.write(f"  ExamType: {name} — {status}")

    def _seed_irregularity_types(self):
        from irregularities.models import IrregularityType

        types = [
            ("Leave", "SECTION_INCHARGE"),
            ("Absence", "SECTION_INCHARGE"),
            ("HW Pendency", "SUBJECT_TEACHER"),
            ("Unpreparedness", "SECTION_INCHARGE"),
            ("Tiffin Issue", "SECTION_INCHARGE"),
            ("Hygiene", "SECTION_INCHARGE"),
            ("Uniform", "SECTION_INCHARGE"),
            ("Gaps in Diary", "SUBJECT_TEACHER"),
            ("Notebook Quality", "SUBJECT_TEACHER"),
            ("Language Skill Gap", "SUBJECT_TEACHER"),
        ]
        for name, role in types:
            obj, created = IrregularityType.objects.get_or_create(
                name=name,
                defaults={"applicable_role": role},
            )
            status = "Created" if created else "Exists"
            self.stdout.write(f"  IrregularityType: {name} — {status}")

    def _seed_grade_mapping(self):
        from core.models import GradeMapping

        grades = [
            (91, 100, "A1"),
            (81, 90, "A2"),
            (71, 80, "B1"),
            (61, 70, "B2"),
            (51, 60, "C1"),
            (41, 50, "C2"),
            (33, 40, "D"),
            (0, 32, "F"),
        ]
        for low, high, grade in grades:
            obj, created = GradeMapping.objects.get_or_create(
                min_percentage=low,
                max_percentage=high,
                defaults={"grade": grade},
            )
            status = "Created" if created else "Exists"
            self.stdout.write(f"  GradeMapping: {low}-{high}% → {grade} — {status}")
