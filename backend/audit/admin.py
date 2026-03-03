"""
EduSync — Audit Admin.
"""
from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "action_type", "model_name", "user", "object_id"]
    list_filter = ["action_type", "model_name"]
    date_hierarchy = "timestamp"
    readonly_fields = [
        "id", "user", "action_type", "model_name", "object_id",
        "old_data", "new_data", "timestamp", "ip_address", "batch_id",
    ]

    def has_add_permission(self, request):
        return False  # Audit logs are system-generated only

    def has_change_permission(self, request, obj=None):
        return False  # Immutable

    def has_delete_permission(self, request, obj=None):
        return False  # Never delete audit logs
