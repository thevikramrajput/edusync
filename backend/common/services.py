"""
EduSync — Service-Layer Audit Helpers.
All critical write paths should go through these functions.
Signals are kept as a fallback, but service functions are the primary audit mechanism.
"""
import uuid as uuid_lib
from threading import local

from django.db import models
from django.forms.models import model_to_dict

_thread_local = local()


def get_current_user():
    """Get current request user from thread-local (set by CurrentUserMiddleware)."""
    return getattr(_thread_local, "user", None)


def set_current_user(user):
    """Set current user in thread-local storage."""
    _thread_local.user = user


def _serialize(instance):
    """Serialize model instance to JSON-safe dict for audit storage."""
    data = model_to_dict(instance)
    result = {}
    for key, value in data.items():
        if isinstance(value, (str, int, float, bool, type(None))):
            result[key] = value
        elif isinstance(value, models.QuerySet):
            result[key] = list(value.values_list("pk", flat=True))
        else:
            result[key] = str(value)
    return result


def audit_log(*, action, instance, old_data=None, new_data=None,
              user=None, batch_id=None):
    """
    Explicit audit log entry. Call from service functions.

    Args:
        action: "CREATE", "UPDATE", or "DELETE"
        instance: The model instance being audited
        old_data: Dict of old field values (for UPDATE/DELETE)
        new_data: Dict of new field values (for CREATE/UPDATE)
        user: The user performing the action (auto-detected if None)
        batch_id: UUID to group related operations (e.g., bulk inserts)
    """
    from audit.models import AuditLog

    AuditLog.objects.create(
        user=user or get_current_user(),
        action_type=action,
        model_name=instance.__class__.__name__,
        object_id=instance.pk,
        old_data=old_data,
        new_data=new_data,
        batch_id=batch_id,
    )


def audit_bulk_create(model_class, objects, user=None):
    """
    Bulk create with audit logging.
    Creates AuditLog entries for each object in the batch.
    Returns list of created objects.
    """
    from audit.models import AuditLog

    batch = uuid_lib.uuid4()
    created = model_class.objects.bulk_create(objects)

    logs = [
        AuditLog(
            user=user or get_current_user(),
            action_type="CREATE",
            model_name=model_class.__name__,
            object_id=obj.pk,
            new_data=_serialize(obj),
            batch_id=batch,
        )
        for obj in created
    ]
    AuditLog.objects.bulk_create(logs)
    return created


def audit_queryset_update(queryset, user=None, **updates):
    """
    QuerySet.update() with audit logging.
    Snapshots affected rows BEFORE update, then logs old→new diff.
    Returns count of updated rows.
    """
    from audit.models import AuditLog

    batch = uuid_lib.uuid4()

    # Snapshot current state before update
    old_snapshots = {obj.pk: _serialize(obj) for obj in queryset}

    # Perform the actual update
    count = queryset.update(**updates)

    # Log all changes
    logs = [
        AuditLog(
            user=user or get_current_user(),
            action_type="UPDATE",
            model_name=queryset.model.__name__,
            object_id=pk,
            old_data=old_data,
            new_data=updates,
            batch_id=batch,
        )
        for pk, old_data in old_snapshots.items()
    ]
    AuditLog.objects.bulk_create(logs)
    return count
