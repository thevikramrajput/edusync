import os
from django.core.management.base import BaseCommand
from accounts.models import User
from core.models import Branch


class Command(BaseCommand):
    help = "Seed test users (Global Admin, Branch Admins) for testing."

    def handle(self, *args, **options):
        # Ensure roles & branches exist
        from django.core.management import call_command
        call_command("seed_initial_data")

        # 1. Global Admin (Super Admin — no branch)
        global_admin, created = User.objects.get_or_create(
            email="admin@edusync.com",
            defaults={
                "first_name": "Global",
                "last_name": "Admin",
                "is_staff": True,
                "is_superuser": True,
                "role_type": User.RoleType.SUPER_ADMIN,
            }
        )
        if created:
            global_admin.set_password("edusync2026")
            global_admin.save()
            self.stdout.write(self.style.SUCCESS("Created Global Admin: admin@edusync.com / edusync2026"))
        else:
            self.stdout.write("Global Admin already exists.")

        # 2. Branch Admins (School Admin — one per branch)
        branches = Branch.objects.all()
        for branch in branches:
            email = f"admin_{branch.code.lower()}@edusync.com"
            branch_admin, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": f"{branch.code}",
                    "last_name": "Admin",
                    "branch": branch,
                    "role_type": User.RoleType.SCHOOL_ADMIN,
                    "is_staff": True,
                }
            )
            if created:
                branch_admin.set_password("edusync2026")
                branch_admin.save()
                self.stdout.write(self.style.SUCCESS(f"Created Branch Admin: {email} / edusync2026"))
            else:
                self.stdout.write(f"Branch Admin {email} already exists.")
