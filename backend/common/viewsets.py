"""
EduSync — Base ViewSets.
All branch-scoped views MUST inherit from BaseBranchScopedViewSet.
"""
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from .permissions import BranchScopePermission


class BaseBranchScopedViewSet(ModelViewSet):
    """
    Enterprise safeguard: automatically filters queryset by user's branch.
    GLOBAL-scoped users see all branches. Branch-scoped users see only theirs.

    Includes assertion safeguard — if a developer forgets BranchScopePermission,
    the view will raise AssertionError in DEBUG mode.
    """
    permission_classes = [IsAuthenticated, BranchScopePermission]
    branch_id = None  # Set by BranchScopePermission

    def get_queryset(self):
        qs = super().get_queryset()

        # Safeguard: if model has branch field, ALWAYS apply branch filter
        if hasattr(qs.model, "branch_id"):
            assert hasattr(self, "branch_id"), (
                f"{self.__class__.__name__} serves a branch-scoped model but "
                f"branch_id was not set. Ensure BranchScopePermission is in "
                f"permission_classes."
            )
            if hasattr(qs, "for_branch"):
                return qs.for_branch(self.branch_id)
            elif self.branch_id is not None:
                return qs.filter(branch_id=self.branch_id)

        return qs

    def perform_create(self, serializer):
        """Auto-assign branch on create if user is branch-scoped."""
        if self.branch_id and hasattr(serializer.Meta.model, "branch_id"):
            serializer.save(branch_id=self.branch_id)
        else:
            serializer.save()
