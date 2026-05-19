"""Django settings for api project - Development environment.

This module contains settings specific to the development environment.
"""

import sys

from .common import *

TESTING = "pytest" in sys.modules or any("pytest" in arg for arg in sys.argv)

# Override session backend for tests — use DB to avoid Redis dependency
# Also use dummy cache to prevent test cache poisoning across tests
if TESTING:
    SESSION_ENGINE = "django.contrib.sessions.backends.db"
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", default=True)

# Allowed hosts for development
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "0.0.0.0", "django"]
)

# Allow Django's test client host during tests
if TESTING:
    ALLOWED_HOSTS += ["testserver"]

# CORS settings for development
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://0.0.0.0:3000",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
]

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

# Add debug toolbar and extensions for development (skip during tests)
if not TESTING:
    INSTALLED_APPS += [
        "debug_toolbar",  # django-debug-toolbar for debugging
    ]
    MIDDLEWARE += [
        "debug_toolbar.middleware.DebugToolbarMiddleware",  # django-debug-toolbar
    ]

INSTALLED_APPS += [
    "django_extensions",  # django-extensions for additional development tools
]

# Email backend for development (console)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Django Debug Toolbar settings
INTERNAL_IPS = [
    "127.0.0.1",
    "0.0.0.0",
]

DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.history.HistoryPanel",
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.alerts.AlertsPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    "debug_toolbar.panels.profiling.ProfilingPanel",
]


# Configure debug toolbar to work with Docker
def show_toolbar(request):  # noqa: ARG001
    return True


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": show_toolbar,
}

# Development-specific logging
LOGGING["loggers"].update(
    {
        "django": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    }
)

# Celery settings for development
CELERY_TASK_ALWAYS_EAGER = env("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_EAGER_PROPAGATES = True

# Django Extensions settings for hot reloading
# Enable automatic reloading of templates and static files
USE_L10N = True
USE_TZ = True

# Auto-reload settings for development server
# This enables automatic reloading when files change
RUNSERVER_PLUS_PRINT_SQL = True

# Additional settings for faster development experience
THUMBNAIL_DEBUG = True

# Enable template debug mode for better error reporting
TEMPLATES[0]["OPTIONS"]["debug"] = True
