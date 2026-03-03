"""
EduSync — Base Models.
All models inherit from BaseModel (UUID PK + soft delete + timestamps).
Branch-scoped models inherit from BranchScopedModel.
"""
import uuid
from django.db import models
from .managers import (
    SoftDeleteManager,
    AllObjectsManager,
    BranchScopedManager,
)


class BaseModel(models.Model):
    """
    Abstract base for ALL EduSync models.
    Provides: UUID primary key, timestamps, soft delete.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    # Default: excludes deleted records
    objects = SoftDeleteManager()
    # Includes deleted records (for admin/audit)
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Override delete to do soft delete by default."""
        self.is_deleted = True
        self.is_active = False
        self.save(update_fields=["is_deleted", "is_active", "updated_at"])

    def soft_delete(self):
        """Explicit soft-delete alias (same as delete)."""
        self.delete()

    def hard_delete(self, using=None, keep_parents=False):
        """Physical deletion — use with extreme caution."""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.is_active = True
        self.save(update_fields=["is_deleted", "is_active", "updated_at"])

    def __str__(self):
        return str(self.id)


class BranchScopedModel(BaseModel):
    """
    Abstract base for models that belong to a specific branch.
    Provides automatic branch-scoped filtering via BranchScopedManager.
    """
    branch = models.ForeignKey(
        "core.Branch",
        on_delete=models.PROTECT,
        related_name="%(class)s_set",
    )

    objects = BranchScopedManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
