"""
EduSync — Custom DRF Exception Handler.
All API errors return a consistent format:

{
    "success": false,
    "error_code": "...",
    "message": "...",
    "details": {...}
}
"""
import logging
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    APIException,
    ValidationError,
    NotFound,
    PermissionDenied,
    AuthenticationFailed,
    Throttled,
)
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger("edusync.security")


def _build_error(error_code, message, details=None, status_code=400):
    """Build standardized error response."""
    return Response(
        {
            "success": False,
            "error_code": error_code,
            "message": message,
            "details": details or {},
        },
        status=status_code,
    )


def custom_exception_handler(exc, context):
    """
    Custom exception handler for all DRF views.
    Logs permission denials and returns consistent JSON errors.
    """

    # ─── Django ValidationError → DRF ValidationError ────
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            exc = ValidationError(detail=exc.message_dict)
        else:
            exc = ValidationError(detail=exc.messages)

    # ─── IntegrityError (DB constraint violation) ────────
    if isinstance(exc, IntegrityError):
        return _build_error(
            error_code="integrity_error",
            message="A database constraint was violated. This record may already exist.",
            details={"db_error": str(exc)},
            status_code=status.HTTP_409_CONFLICT,
        )

    # ─── Let DRF handle it first ────────────────────────
    response = exception_handler(exc, context)

    if response is None:
        # Unhandled exception — log and return 500
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return _build_error(
            error_code="internal_error",
            message="An unexpected error occurred. Please try again later.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # ─── Map known exceptions to our format ──────────────
    if isinstance(exc, ValidationError):
        return _build_error(
            error_code="validation_error",
            message="One or more fields failed validation.",
            details=response.data,
            status_code=response.status_code,
        )

    if isinstance(exc, NotFound):
        return _build_error(
            error_code="not_found",
            message=str(exc.detail),
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, PermissionDenied):
        # Log permission denial for security monitoring
        request = context.get("request")
        user = getattr(request, "user", None)
        logger.warning(
            f"Permission denied: user={getattr(user, 'email', 'anonymous')} "
            f"path={getattr(request, 'path', 'unknown')} "
            f"method={getattr(request, 'method', 'unknown')}"
        )
        return _build_error(
            error_code="permission_denied",
            message="You do not have permission to perform this action.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if isinstance(exc, AuthenticationFailed):
        return _build_error(
            error_code="authentication_failed",
            message="Authentication credentials were invalid or not provided.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if isinstance(exc, Throttled):
        return _build_error(
            error_code="throttled",
            message=f"Request was throttled. Try again in {exc.wait:.0f} seconds.",
            details={"retry_after": exc.wait},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    # ─── Generic APIException fallback ───────────────────
    return _build_error(
        error_code="api_error",
        message=str(exc.detail) if hasattr(exc, "detail") else "An error occurred.",
        details=response.data if response else {},
        status_code=response.status_code if response else status.HTTP_400_BAD_REQUEST,
    )
