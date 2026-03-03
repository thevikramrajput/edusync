import os
from django.core.management.base import BaseCommand
from accounts.models import User, Role
from core.models import Branch

class Command(BaseCommand):
    help = "Seed test users (Global Admin, Branch Admins) for testing."

    def handle(self, *args, **options):
        # Ensure roles exist
        from django.core.management import call_command
        call_command("seed_initial_data")

        principal_role = Role.objects.get(name="PRINCIPAL")

        # 1. Global Admin
        global_admin, created = User.objects.get_or_create(
            email="admin@edusync.com",
            defaults={
                "first_name": "Global",
                "last_name": "Admin",
                "is_staff": True,
                "is_superuser": True,
                "role": principal_role,
            }
        )
        if created:
            global_admin.set_password("edusync2026")
            global_admin.save()
            self.stdout.write(self.style.SUCCESS("Created Global Admin: admin@edusync.com / edusync2026"))
        else:
            self.stdout.write("Global Admin already exists.")

        # 2. Branch Admins
        branches = Branch.objects.all()
        for branch in branches:
            email = f"admin_{branch.code.lower()}@edusync.com"
            branch_admin, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": f"{branch.code}",
                    "last_name": "Admin",
                    "branch": branch,
                    "role": principal_role,
                    "is_staff": True,
                }
            )
            if created:
                branch_admin.set_password("edusync2026")
                branch_admin.save()
                self.stdout.write(self.style.SUCCESS(f"Created Branch Admin: {email} / edusync2026"))
            else:
                self.stdout.write(f"Branch Admin {email} already exists.")
