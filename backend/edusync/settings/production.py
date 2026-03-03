"""
EduSync — Production Settings (security hardened).
Use: DJANGO_SETTINGS_MODULE=edusync.settings.production
"""
import os
from .base import *  # noqa: F401, F403

# ─── Core ────────────────────────────────────────────────
DEBUG = False

# ─── HTTPS Enforcement ───────────────────────────────────
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000       # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ─── Cookie Security ────────────────────────────────────
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# ─── Security Headers ───────────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# ─── Password Hashers (production-grade, NO MD5) ────────
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

# ─── CORS (restrict to frontend domain) ─────────────────
CORS_ALLOW_ALL_ORIGINS = False
# CORS_ALLOWED_ORIGINS already set from base.py via FRONTEND_URL env var

# ─── Tighter Throttling ─────────────────────────────────
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "10/minute",
    "user": "60/minute",
}

# ─── Production Logging ─────────────────────────────────
LOGGING["formatters"]["production"] = {  # noqa: F405
    "format": "[{asctime}] {levelname} {name} | {message}",
    "style": "{",
    "datefmt": "%Y-%m-%d %H:%M:%S",
}
LOGGING["handlers"]["console"]["formatter"] = "production"  # noqa: F405
LOGGING["loggers"]["django"]["level"] = "WARNING"  # noqa: F405
LOGGING["loggers"]["edusync"]["level"] = "INFO"  # noqa: F405
