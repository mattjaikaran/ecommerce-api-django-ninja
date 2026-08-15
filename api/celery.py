"""Celery configuration for the api project."""

import logging
import os

from celery import Celery
from celery.signals import task_failure, task_postrun, task_prerun

from api.middleware.request_id import request_id_var

logger = logging.getLogger(__name__)

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings.dev")

app = Celery("api")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure Celery Beat
app.conf.beat_schedule = {
    "cleanup-expired-sessions": {
        "task": "core.tasks.cleanup_expired_sessions",
        "schedule": 3600.0,  # hourly
    },
    "cleanup-expired-carts": {
        "task": "cart.tasks.cleanup_expired_carts",
        "schedule": 3600.0,  # hourly
    },
    "cleanup-expired-idempotency-keys": {
        "task": "orders.tasks.cleanup_expired_idempotency_keys",
        "schedule": 86400.0,  # daily
    },
    "send-abandoned-cart-emails": {
        "task": "cart.tasks.send_abandoned_cart_emails",
        "schedule": 3600.0,  # hourly — checks carts idle for 2+ hours
    },
    "low-stock-alerts": {
        "task": "products.tasks.send_low_stock_alerts",
        "schedule": 21600.0,  # every 6 hours
    },
    "out-of-stock-alerts": {
        "task": "products.tasks.send_out_of_stock_alerts",
        "schedule": 21600.0,  # every 6 hours
    },
    "daily-sales-rollup": {
        "task": "analytics.tasks.rollup_daily_sales",
        "schedule": 86400.0,  # daily
    },
    "daily-product-analytics-rollup": {
        "task": "analytics.tasks.rollup_product_analytics",
        "schedule": 86400.0,  # daily
    },
}

app.conf.timezone = "UTC"


@task_prerun.connect
def restore_request_id(sender=None, task=None, **_):  # noqa: ARG001
    """Restore the originating request id into the worker context."""
    headers = getattr(getattr(task, "request", None), "headers", None) or {}
    request_id = headers.get("x_request_id")
    if request_id:
        request_id_var.set(request_id)


@task_postrun.connect
def clear_request_id(**kwargs):  # noqa: ARG001
    """Clear the request id so stale values never leak across tasks."""
    request_id_var.set("")


@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, **_):
    """Route tasks that have exhausted all retries to the dead_letter queue."""
    retries = getattr(sender, "request", None)
    max_retries = getattr(sender, "max_retries", None)
    current_retries = getattr(retries, "retries", None) if retries else None

    if max_retries is not None and current_retries is not None and current_retries >= max_retries:
        task_name = getattr(sender, "name", "unknown")
        logger.error(
            "task_dead_lettered",
            extra={
                "task_id": task_id,
                "task_name": task_name,
                "retries": current_retries,
                "exception": str(exception),
            },
        )
        # Re-publish to dead_letter queue for inspection / manual replay
        app.send_task(
            "dead_letter.task",
            args=[task_name, task_id, str(exception)],
            queue="dead_letter",
        )


@app.task(bind=True, ignore_result=True, name="dead_letter.task", queue="dead_letter")
def dead_letter_sink(self, task_name: str, task_id: str, error: str):  # noqa: ARG001
    """Receives tasks that exhausted all retries. Logs for alerting/replay."""
    logger.critical(
        "dead_letter_received",
        extra={"original_task": task_name, "original_task_id": task_id, "error": error},
    )


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.info("celery_debug_task_executed", extra={"request": repr(self.request)})
