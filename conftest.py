import pytest
from django.test import Client


def _kill_test_db_connections():
    """Kill all connections to test_ecommerce_db via the postgres maintenance DB."""
    try:
        import os
        import psycopg2
        conn = psycopg2.connect(
            dbname=os.environ.get("MAINTENANCE_DB", "postgres"),
            user=os.environ.get("DB_USER", os.environ.get("USER", "")),
            password=os.environ.get("DB_PASSWORD", ""),
            host=os.environ.get("DB_HOST", "localhost"),
            port=int(os.environ.get("DB_PORT", 5432)),
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = %s AND pid <> pg_backend_pid()",
            ["test_ecommerce_db"],
        )
        cur.close()
        conn.close()
    except Exception:
        pass  # Non-fatal: stale connection cleanup is best-effort


def pytest_sessionstart(session):
    """Kill stale connections to the test database before pytest creates it."""
    _kill_test_db_connections()


@pytest.fixture
def api_client():
    """Return Django test client for API testing."""
    return Client()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Give all tests access to the database.

    This fixture automatically applies to all tests and ensures database access.
    """


@pytest.fixture
def transactional_db(db):
    """Create a transactional database for tests that need transaction testing."""


@pytest.fixture(autouse=True)
def allow_test_server_host(settings):
    """Add 'testserver' to ALLOWED_HOSTS so Django test client requests are accepted."""
    if "testserver" not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver"]
    # Switch session backend from Redis cache to DB so force_login works without Redis.
    settings.SESSION_ENGINE = "django.contrib.sessions.backends.db"
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }
    # Close connections after each test to avoid leaving idle-in-transaction sessions
    # that block the test DB from being dropped on teardown.
    settings.CONN_MAX_AGE = 0


