"""
EduSync — Custom Middleware.
CurrentUserMiddleware: thread-local user for audit.
RequestLoggingMiddleware: logs method, path, user, branch, response time.
"""
import time
import logging
from .services import set_current_user

logger = logging.getLogger("edusync.requests")


class CurrentUserMiddleware:
    """
    Stores request.user in thread-local storage so that service-layer
    audit functions can access the current user without requiring it
    as an explicit parameter.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, "user") and request.user.is_authenticated:
            set_current_user(request.user)
        else:
            set_current_user(None)

        response = self.get_response(request)

        # Clean up thread-local after request
        set_current_user(None)
        return response


class RequestLoggingMiddleware:
    """
    Logs every API request with:
    method, path, user_id, branch_id, status_code, response_time_ms.

    Placed after AuthenticationMiddleware so request.user is populated.
    Excludes health check and static file requests.
    """

    EXCLUDED_PREFIXES = ("/static/", "/favicon.ico")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        elapsed_ms = (time.monotonic() - start) * 1000

        # Skip static/non-API requests
        path = request.path
        if any(path.startswith(prefix) for prefix in self.EXCLUDED_PREFIXES):
            return response

        user_id = "-"
        branch_id = "-"
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = str(request.user.pk)
            branch_id = str(getattr(request.user, "branch_id", None) or "-")

        logger.info(
            "%s %s | user=%s branch=%s | %s %.0fms",
            request.method,
            path,
            user_id,
            branch_id,
            response.status_code,
            elapsed_ms,
        )

        return response
