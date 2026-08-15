"""Tests for health check endpoints and service probes."""

from unittest.mock import MagicMock

import pytest
from django.test import Client

from api import healthcheck

pytestmark = pytest.mark.django_db


class FakeRedis:
    """In-memory stand-in for a Redis client."""

    def ping(self):
        return True


class FakeCache:
    """In-memory stand-in for Django's cache backend."""

    def __init__(self):
        self._data = {}

    def set(self, key, value, _timeout):
        self._data[key] = value

    def get(self, key):
        return self._data.get(key)

    def delete(self, key):
        self._data.pop(key, None)


def _patch_healthy_probes(monkeypatch):
    """Patch the database/redis/celery/migrations probes to report healthy."""
    monkeypatch.setattr(
        healthcheck.HealthChecker,
        "_check_database",
        lambda _self: {"status": "healthy", "message": "ok"},
    )
    monkeypatch.setattr(
        healthcheck.HealthChecker,
        "_check_redis",
        lambda _self: {"status": "healthy", "message": "ok"},
    )
    monkeypatch.setattr(
        healthcheck.HealthChecker,
        "_check_celery",
        lambda _self: {"status": "healthy", "message": "ok"},
    )
    monkeypatch.setattr(
        healthcheck.HealthChecker,
        "_check_migrations",
        lambda _self: {"status": "healthy", "message": "ok"},
    )


def test_health_check_simple_returns_200():
    response = Client().get("/health/")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_liveness_returns_200():
    response = Client().get("/liveness/")

    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_readiness_returns_200_when_critical_healthy(monkeypatch):
    _patch_healthy_probes(monkeypatch)

    response = Client().get("/readiness/")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readiness_returns_503_when_db_fails(monkeypatch):
    _patch_healthy_probes(monkeypatch)
    monkeypatch.setattr(
        healthcheck.HealthChecker,
        "_check_database",
        lambda _self: {"status": "unhealthy", "message": "db down"},
    )

    response = Client().get("/readiness/")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"


def test_redis_check_healthy(monkeypatch):
    monkeypatch.setattr(healthcheck, "get_redis_connection", lambda _alias: FakeRedis())
    monkeypatch.setattr(healthcheck, "cache", FakeCache())

    result = healthcheck.HealthChecker()._check_redis()  # noqa: SLF001

    assert result["status"] == "healthy"


def test_redis_check_unhealthy(monkeypatch):
    redis_client = MagicMock()
    redis_client.ping.side_effect = ConnectionError("Redis is down")
    monkeypatch.setattr(
        healthcheck, "get_redis_connection", lambda _alias: redis_client
    )
    monkeypatch.setattr(healthcheck, "cache", FakeCache())

    result = healthcheck.HealthChecker()._check_redis()  # noqa: SLF001

    assert result["status"] == "unhealthy"
    assert "Redis connection failed" in result["message"]


def test_celery_check_healthy(monkeypatch):
    app = MagicMock()
    app.control.ping.return_value = [{"worker1": {"ok": "pong"}}]
    monkeypatch.setattr(healthcheck, "current_app", app)

    result = healthcheck.HealthChecker()._check_celery()  # noqa: SLF001

    assert result["status"] == "healthy"
    assert "1 worker" in result["message"]


def test_celery_check_unhealthy(monkeypatch):
    app = MagicMock()
    app.control.ping.return_value = []
    monkeypatch.setattr(healthcheck, "current_app", app)

    result = healthcheck.HealthChecker()._check_celery()  # noqa: SLF001

    assert result["status"] == "unhealthy"
    assert "No Celery workers" in result["message"]


def test_celery_check_unhealthy_when_ping_fails(monkeypatch):
    app = MagicMock()
    app.control.ping.side_effect = ConnectionError("broker unreachable")
    monkeypatch.setattr(healthcheck, "current_app", app)

    result = healthcheck.HealthChecker()._check_celery()  # noqa: SLF001

    assert result["status"] == "unhealthy"
    assert "Celery ping failed" in result["message"]


def test_migration_check_healthy(monkeypatch):
    recorder = MagicMock()
    recorder.applied_migrations.return_value = {
        ("orders", "0001_initial"): MagicMock(),
        ("orders", "0002_x"): MagicMock(),
    }
    monkeypatch.setattr(healthcheck, "MigrationRecorder", lambda: recorder)
    loader = MagicMock()
    loader.disk_migrations = {
        ("orders", "0001_initial"): MagicMock(),
        ("orders", "0002_x"): MagicMock(),
    }
    monkeypatch.setattr(healthcheck, "MigrationLoader", MagicMock(return_value=loader))

    result = healthcheck.HealthChecker()._check_migrations()  # noqa: SLF001

    assert result["status"] == "healthy"


def test_migration_check_unhealthy(monkeypatch):
    recorder = MagicMock()
    recorder.applied_migrations.return_value = {
        ("orders", "0001_initial"): MagicMock(),
    }
    monkeypatch.setattr(healthcheck, "MigrationRecorder", lambda: recorder)
    loader = MagicMock()
    loader.disk_migrations = {
        ("orders", "0001_initial"): MagicMock(),
        ("orders", "0002_x"): MagicMock(),
    }
    monkeypatch.setattr(healthcheck, "MigrationLoader", MagicMock(return_value=loader))

    result = healthcheck.HealthChecker()._check_migrations()  # noqa: SLF001

    assert result["status"] == "unhealthy"
    assert "orders.0002_x" in result["message"]


def test_email_check_skipped_in_dev():
    result = healthcheck.HealthChecker()._check_email()  # noqa: SLF001

    assert result["status"] == "skipped"


def test_check_all_reports_healthy_with_skipped_services(monkeypatch):
    _patch_healthy_probes(monkeypatch)

    response = Client().get("/health/all/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["summary"]["unhealthy"] == 0
    assert data["summary"]["skipped"] >= 1


def test_check_all_reports_unhealthy_when_probe_fails(monkeypatch):
    _patch_healthy_probes(monkeypatch)
    monkeypatch.setattr(
        healthcheck.HealthChecker,
        "_check_database",
        lambda _self: {"status": "unhealthy", "message": "db down"},
    )

    response = Client().get("/health/all/")

    assert response.status_code == 503
    assert response.json()["status"] == "unhealthy"


def test_unknown_service_returns_503():
    response = Client().get("/health/doesnotexist/")

    assert response.status_code == 503
    assert response.json()["status"] == "unknown"
