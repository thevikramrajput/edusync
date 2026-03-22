"""
EduSync — Audit Signals (Fallback).
Catches direct .save() calls that bypass service functions.
Primary audit logging is done via common.services.audit_log().
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict

from audit.models import AuditLog
from common.services import get_current_user


# Models to auto-audit via signals (fallback for direct .save() calls)
AUDITED_MODELS = []


def _register_audited_models():
    """Lazy import to avoid circular imports."""
    global AUDITED_MODELS
    if not AUDITED_MODELS:
        from exams.models import ExamMark
        from assessments.models import StudentAssessmentScore
        from irregularities.models import StudentIrregularity
        from lesson_plans.models import DailyLessonPlan
        AUDITED_MODELS = [ExamMark, StudentAssessmentScore,
                          StudentIrregularity, DailyLessonPlan]


def _safe_serialize(instance):
    try:
        data = model_to_dict(instance)
        return {
            k: str(v) if not isinstance(v, (str, int, float, bool, type(None)))
            else v
            for k, v in data.items()
        }
    except Exception:
        return {"id": str(instance.pk)}


@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    """Capture old state before save for audit diff."""
    _register_audited_models()
    if sender not in AUDITED_MODELS:
        return

    if instance.pk:
        try:
            old_instance = sender.all_objects.get(pk=instance.pk)
            instance._audit_old_data = _safe_serialize(old_instance)
        except sender.DoesNotExist:
            instance._audit_old_data = None
    else:
        instance._audit_old_data = None


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    """Log changes after save."""
    _register_audited_models()
    if sender not in AUDITED_MODELS:
        return

    old_data = getattr(instance, "_audit_old_data", None)
    new_data = _safe_serialize(instance)

    # Skip if this was already logged via service function
    # (Service functions log with explicit user; signal logs with thread-local)
    AuditLog.objects.create(
        user=get_current_user(),
        action_type="CREATE" if created else "UPDATE",
        model_name=sender.__name__,
        object_id=instance.pk,
        old_data=old_data,
        new_data=new_data,
    )
