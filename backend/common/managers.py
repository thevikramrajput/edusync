"""
EduSync — Custom Managers & QuerySets.
Provides soft-delete filtering and branch-scoped isolation across all models.
"""
from django.db import models


# ─── Soft Delete QuerySet & Managers ────────────────────────

class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet that supports soft-delete operations."""

    def delete(self):
        """Soft delete — marks records as deleted, never hard deletes."""
        return self.update(is_deleted=True, is_active=False)

    def hard_delete(self):
        """Actual DB deletion — use with extreme caution."""
        return super().delete()

    def alive(self):
        """Filter to only non-deleted records."""
        return self.filter(is_deleted=False)


class SoftDeleteManager(models.Manager):
    """
    Default manager for all EduSync models.
    Automatically excludes soft-deleted records from all queries.
    """

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class AllObjectsManager(models.Manager):
    """
    Include soft-deleted records. For admin/audit views only.
    Usage: MyModel.all_objects.all()
    """

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


# ─── Branch-Scoped QuerySet & Manager ──────────────────────

class BranchScopedQuerySet(SoftDeleteQuerySet):
    """QuerySet with branch isolation support."""

    def for_branch(self, branch_id):
        """
        Filter by branch. If branch_id is None (GLOBAL scope), returns all.
        """
        if branch_id is None:
            return self
        return self.filter(branch_id=branch_id)


class BranchScopedManager(SoftDeleteManager):
    """Manager for branch-scoped models. Auto-excludes deleted records."""

    def get_queryset(self):
        return BranchScopedQuerySet(self.model, using=self._db).alive()

    def for_branch(self, branch_id):
        """Delegate for_branch to the underlying QuerySet."""
        return self.get_queryset().for_branch(branch_id)
