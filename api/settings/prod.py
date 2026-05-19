"""Django settings for api project - Production environment.

This module contains settings specific to the production environment.
"""

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from .common import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", default=False)

# Sentry — only initialise when DSN is configured
_sentry_dsn = env("SENTRY_DSN", default="")
if _sentry_dsn:
    import logging

    sentry_sdk.init(
        dsn=_sentry_dsn,
        environment=env("SENTRY_ENVIRONMENT", default="production"),
        integrations=[
            DjangoIntegration(transaction_style="url"),
            CeleryIntegration(monitor_beat_tasks=True),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR,
            ),
        ],
        traces_sample_rate=env("SENTRY_TRACES_SAMPLE_RATE", default=0.1),
        profiles_sample_rate=env("SENTRY_PROFILES_SAMPLE_RATE", default=0.1),
        send_default_pii=False,
    )

# Production allowed hosts
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# CORS settings for production
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# SSL settings
USE_TLS = env("USE_TLS", default=True)
if USE_TLS:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Email backend for production
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@example.com")

# File storage for production (can be configured for S3, etc.)
# Uncomment and configure if using AWS S3
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

# AWS S3 settings (if used)
# AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
# AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
# AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="")
# AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
# AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default="")
# AWS_DEFAULT_ACL = None
# AWS_S3_OBJECT_PARAMETERS = {
#     'CacheControl': 'max-age=86400',
# }

# Production logging — JSON to stdout (parseable by any log aggregator)
LOGGING["handlers"]["console"]["formatter"] = "json"
LOGGING["handlers"].update(
    {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "/app/logs/django.log",
            "formatter": "json",
        },
    }
)

LOGGING["loggers"].update(
    {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "file"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
        "orders": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "cart": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "products": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "analytics": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "payments": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    }
)

# Celery settings for production
CELERY_TASK_ALWAYS_EAGER = False
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Database connection pooling for production
DATABASES["default"].update(
    {
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "MAX_CONNS": 20,
            "MIN_CONNS": 5,
        },
    }
)

# Cache configuration for production with connection pooling
CACHES["default"]["OPTIONS"].update(
    {
        "CONNECTION_POOL_KWARGS": {
            "max_connections": 50,
            "retry_on_timeout": True,
        }
    }
)

# Session security for production
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
if USE_TLS:
    SESSION_COOKIE_SECURE = True

# CSRF security for production
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
if USE_TLS:
    CSRF_COOKIE_SECURE = True
