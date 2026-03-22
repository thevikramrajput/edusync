"""
EduSync — Development Settings.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# Relaxed CORS for development
CORS_ALLOW_ALL_ORIGINS = True

# Relaxed throttling for development
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "1000/minute",
    "user": "5000/minute",
}

# Fast password hasher for tests (NOT for production)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
