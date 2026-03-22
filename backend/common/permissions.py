"""
EduSync — DRF Permission Classes.
Enforces branch-level data isolation and role-based access.
"""
from rest_framework.permissions import BasePermission


class BranchScopePermission(BasePermission):
    """
    Injects `branch_id` into the view for automatic queryset filtering.
    - Superusers & GLOBAL-scoped faculty: branch_id = None (see all branches)
    - Branch-scoped users: branch_id = their branch
    """

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False

        # Superusers see everything
        if user.is_superuser:
            view.branch_id = None
            return True

        # Check if faculty has GLOBAL scope
        if hasattr(user, "faculty_profile"):
            from accounts.models import FacultyRoleMapping
            is_global = FacultyRoleMapping.objects.filter(
                faculty=user.faculty_profile,
                scope_type="GLOBAL",
                is_deleted=False,
            ).exists()
            if is_global:
                view.branch_id = None
                return True

        # Branch-scoped: inject user's branch
        branch_id = getattr(user, "branch_id", None)
        if branch_id is None:
            return False

        view.branch_id = branch_id
        return True


class RoleBasedPermission(BasePermission):
    """
    Checks if the user's role has a specific permission key.
    Views should set `required_permission` attribute.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        required_perm = getattr(view, "required_permission", None)
        if required_perm is None:
            return True  # No specific permission required

        if not hasattr(user, "faculty_profile"):
            return False

        from accounts.models import RolePermission
        faculty = user.faculty_profile
        role_ids = faculty.role_mappings.values_list("role_id", flat=True)
        return RolePermission.objects.filter(
            role_id__in=role_ids,
            permission_key=required_perm,
            is_deleted=False,
        ).exists()
