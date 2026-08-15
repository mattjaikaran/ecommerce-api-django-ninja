"""Health check module for the ecommerce API.

This module provides health check endpoints and utilities to monitor
the status of various services and dependencies.
"""

import time
from datetime import UTC, datetime
from typing import Any

from celery import current_app
from django.conf import settings
from django.core.cache import cache
from django.core.mail import get_connection
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder
from django.http import JsonResponse
from django_redis import get_redis_connection

from .config.constants import HEALTH_CHECK_SERVICES


class HealthChecker:
    """Health check utility class."""

    def __init__(self):
        self.checks = {
            "database": self._check_database,
            "redis": self._check_redis,
            "s3": self._check_s3,
            "stripe": self._check_stripe,
            "email": self._check_email,
            "celery": self._check_celery,
            "migrations": self._check_migrations,
        }

    def check_all(self) -> dict[str, Any]:
        """Run all health checks."""
        results = {
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "services": {},
            "summary": {
                "total": len(HEALTH_CHECK_SERVICES),
                "healthy": 0,
                "unhealthy": 0,
                "skipped": 0,
            },
        }

        overall_healthy = True

        for service in HEALTH_CHECK_SERVICES:
            if service in self.checks:
                start_time = time.time()
                check_result = self.checks[service]()
                end_time = time.time()

                results["services"][service] = {
                    **check_result,
                    "response_time_ms": round((end_time - start_time) * 1000, 2),
                }

                if check_result["status"] == "healthy":
                    results["summary"]["healthy"] += 1
                elif check_result["status"] == "skipped":
                    results["summary"]["skipped"] += 1
                else:
                    results["summary"]["unhealthy"] += 1
                    overall_healthy = False
            else:
                results["services"][service] = {
                    "status": "unknown",
                    "message": "No health check implemented",
                }
                results["summary"]["unhealthy"] += 1
                overall_healthy = False

        results["status"] = "healthy" if overall_healthy else "unhealthy"
        return results

    def check_service(self, service_name: str) -> dict[str, Any]:
        """Check a specific service."""
        if service_name not in self.checks:
            return {
                "status": "unknown",
                "message": f"No health check for service: {service_name}",
            }

        start_time = time.time()
        result = self.checks[service_name]()
        end_time = time.time()

        result["response_time_ms"] = round((end_time - start_time) * 1000, 2)
        return result

    def _check_database(self) -> dict[str, Any]:
        """Check database connectivity."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

            return {"status": "healthy", "message": "Database connection successful"}
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {e!s}",
            }

    def _check_redis(self) -> dict[str, Any]:
        """Check Redis connectivity with a direct PING plus a cache round-trip."""
        try:
            get_redis_connection("default").ping()
        except Exception as e:
            return {"status": "unhealthy", "message": f"Redis connection failed: {e!s}"}
        try:
            test_key = "healthcheck:redis:test"
            test_value = "test_value"
            cache.set(test_key, test_value, 60)
            retrieved_value = cache.get(test_key)
            cache.delete(test_key)
            if retrieved_value != test_value:
                return {
                    "status": "unhealthy",
                    "message": "Redis data integrity check failed",
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Redis data integrity check failed: {e!s}",
            }
        return {"status": "healthy", "message": "Redis connection successful"}

    def _check_s3(self) -> dict[str, Any]:
        """Check S3 connectivity."""
        try:
            if not getattr(settings, "USE_S3", False):
                return {"status": "skipped", "message": "S3 not configured"}

            from django.core.files.storage import default_storage

            # Try to list files in the bucket
            default_storage.listdir("")

            return {"status": "healthy", "message": "S3 connection successful"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"S3 connection failed: {e!s}"}

    def _check_stripe(self) -> dict[str, Any]:
        """Check Stripe connectivity."""
        try:
            stripe_key = getattr(settings, "STRIPE_SECRET_KEY", None)
            if not stripe_key:
                return {"status": "skipped", "message": "Stripe not configured"}

            import stripe

            stripe.api_key = stripe_key

            # Make a simple API call to check connectivity
            stripe.Account.retrieve()

            return {"status": "healthy", "message": "Stripe connection successful"}
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Stripe connection failed: {e!s}",
            }

    def _check_email(self) -> dict[str, Any]:
        """Check SMTP connectivity; skipped when no SMTP backend is configured."""
        backend = getattr(settings, "EMAIL_BACKEND", "")
        if "console" in backend or "locmem" in backend:
            return {"status": "skipped", "message": "Email backend is development-only"}
        host = getattr(settings, "EMAIL_HOST", None)
        if not host:
            return {"status": "skipped", "message": "Email not configured"}
        try:
            smtp_connection = get_connection()
            smtp_connection.open()
            smtp_connection.close()
        except Exception as e:
            return {"status": "unhealthy", "message": f"Email connection failed: {e!s}"}
        return {"status": "healthy", "message": "Email connection successful"}

    def _check_celery(self) -> dict[str, Any]:
        """Check Celery worker liveness via control.ping."""
        try:
            responses = current_app.control.ping(timeout=2)
        except Exception as e:
            return {"status": "unhealthy", "message": f"Celery ping failed: {e!s}"}
        if responses:
            return {
                "status": "healthy",
                "message": f"{len(responses)} worker(s) responded",
            }
        return {"status": "unhealthy", "message": "No Celery workers responded"}

    def _check_migrations(self) -> dict[str, Any]:
        """Check that no migrations are unapplied (drift probe)."""
        try:
            applied = MigrationRecorder().applied_migrations()
            loader = MigrationLoader(connection, ignore_no_migrations=True)
            unapplied = [
                (app, name)
                for (app, name) in loader.disk_migrations
                if (app, name) not in applied
            ]
            if not unapplied:
                return {"status": "healthy", "message": "All migrations applied"}
            names = [f"{app}.{name}" for app, name in unapplied]
            return {
                "status": "unhealthy",
                "message": f"Unapplied migrations: {', '.join(names)}",
            }
        except Exception as e:
            return {"status": "unhealthy", "message": f"Migration check failed: {e!s}"}


# Health check views


def health_check_all(request):
    """Endpoint for checking all services."""
    checker = HealthChecker()
    results = checker.check_all()

    status_code = 200 if results["status"] == "healthy" else 503
    return JsonResponse(results, status=status_code)


def health_check_simple(request):
    """Simple health check endpoint."""
    return JsonResponse(
        {
            "status": "healthy",
            "message": "API is running",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


def health_check_service(request, service_name):
    """Endpoint for checking a specific service."""
    checker = HealthChecker()
    result = checker.check_service(service_name)

    status_code = 200 if result["status"] in ("healthy", "skipped") else 503
    return JsonResponse({"service": service_name, **result}, status=status_code)


def readiness_check(request):
    """Readiness check for Kubernetes/container orchestration."""
    checker = HealthChecker()

    # Check critical services only
    critical_services = ["database", "redis", "celery"]
    all_ready = True

    for service in critical_services:
        result = checker.check_service(service)
        if result["status"] != "healthy":
            all_ready = False
            break

    if all_ready:
        return JsonResponse(
            {"status": "ready", "message": "Service is ready to receive traffic"}
        )
    return JsonResponse(
        {"status": "not_ready", "message": "Service is not ready to receive traffic"},
        status=503,
    )


def liveness_check(request):
    """Liveness check for Kubernetes/container orchestration."""
    # Simple check to see if the application is still running
    return JsonResponse(
        {
            "status": "alive",
            "message": "Service is alive",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


# Utility functions


def get_system_info() -> dict[str, Any]:
    """Get system information."""
    import platform
    import sys

    import django

    return {
        "python_version": sys.version,
        "django_version": django.get_version(),
        "platform": platform.platform(),
        "architecture": platform.architecture(),
        "hostname": platform.node(),
    }


def get_database_info() -> dict[str, Any]:
    """Get database information."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]

        return {
            "engine": connection.vendor,
            "version": version,
            "database": connection.settings_dict["NAME"],
        }
    except Exception as e:
        return {"error": str(e)}


def monitoring_info(request):
    """Comprehensive monitoring information."""
    checker = HealthChecker()

    return JsonResponse(
        {
            "health": checker.check_all(),
            "system": get_system_info(),
            "database": get_database_info(),
            "settings": {
                "debug": settings.DEBUG,
                "allowed_hosts": settings.ALLOWED_HOSTS,
                "time_zone": settings.TIME_ZONE,
            },
        }
    )
