"""
EduSync — Audit Log System.
Stores all critical data changes for accountability and compliance.
"""
import uuid
from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """
    Immutable audit trail. Populated by:
    1. Service-layer functions (primary) — handles bulk ops, queryset updates
    2. Django signals (fallback) — catches direct .save() calls
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action_type = models.CharField(
        max_length=10,
        help_text="CREATE, UPDATE, or DELETE.",
    )
    model_name = models.CharField(max_length=100, db_index=True)
    object_id = models.UUIDField(db_index=True)
    old_data = models.JSONField(null=True, blank=True)
    new_data = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    batch_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Groups related operations (e.g., bulk inserts).",
    )

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["model_name", "object_id"]),
            models.Index(fields=["user", "timestamp"]),
        ]

    def __str__(self):
        return f"[{self.action_type}] {self.model_name}:{self.object_id} by {self.user}"
