"""Tests for X-Request-ID middleware, logging filter, and Celery propagation."""

import logging
from decimal import Decimal
from types import SimpleNamespace

import pytest
from celery.app.task import Context
from django.test import Client

from api.celery import clear_request_id, restore_request_id
from api.middleware.request_id import request_id_var
from core.tests.factories import CustomerFactory, UserFactory
from loyalty.tasks import credit_order_points
from orders.tests.factories import OrderFactory

pytestmark = pytest.mark.django_db


def test_provided_header_is_echoed():
    """The incoming X-Request-ID header is echoed back on the response."""
    client = Client()
    resp = client.get("/health/", HTTP_X_REQUEST_ID="req-abc-123")

    assert resp.status_code == 200
    assert resp.headers["X-Request-ID"] == "req-abc-123"


def test_absent_header_generates_one():
    """A missing header produces a generated request id on the response."""
    client = Client()
    resp = client.get("/health/")

    assert resp.status_code == 200
    assert len(resp.headers["X-Request-ID"]) > 0


def test_header_value_is_sanitized():
    """Invalid characters are stripped and the length is capped at 100."""
    client = Client()
    resp = client.get("/health/", HTTP_X_REQUEST_ID=" bad\nid<>! ")

    assert resp.status_code == 200
    request_id = resp.headers["X-Request-ID"]
    assert " " not in request_id
    assert "\n" not in request_id
    assert "<" not in request_id
    assert ">" not in request_id

    long_resp = client.get("/health/", HTTP_X_REQUEST_ID="a" * 500)
    assert long_resp.status_code == 200
    assert len(long_resp.headers["X-Request-ID"]) == 100


def test_log_records_carry_request_id(caplog):
    """Log records emitted during a request carry the request id."""
    client = Client()
    user = UserFactory()
    client.force_login(user)

    with caplog.at_level(logging.INFO):
        resp = client.get("/api/products", HTTP_X_REQUEST_ID="req-log-9")

    assert resp.status_code == 200
    decorator_records = [r for r in caplog.records if r.name == "api.decorators"]
    assert decorator_records
    assert all(r.request_id == "req-log-9" for r in decorator_records)


def test_worker_signals_restore_and_clear_request_id():
    """The prerun signal restores the id and postrun clears it."""
    fake_task = SimpleNamespace(
        request=Context(
            {
                "x_request_id": "task-xyz",
                "id": "t1",
                "task": "loyalty.tasks.credit_order_points",
            },
            args=(),
            called_directly=False,
            kwargs={},
        )
    )
    try:
        restore_request_id(
            sender=None, task=fake_task, task_id="t1", args=(), kwargs={}
        )
        assert request_id_var.get() == "task-xyz"
    finally:
        clear_request_id()
    assert request_id_var.get() == ""


def test_task_logs_carry_originating_request_id(caplog):
    """Task log records carry the request id set in the caller context."""
    customer = CustomerFactory()
    order = OrderFactory(customer=customer, total=Decimal("25.00"))

    token = request_id_var.set("req-task-7")
    try:
        with caplog.at_level(logging.INFO):
            credit_order_points(order.id)
    finally:
        request_id_var.reset(token)

    credited_records = [
        r for r in caplog.records if "loyalty points credited" in r.getMessage()
    ]
    assert credited_records
    assert all(r.request_id == "req-task-7" for r in credited_records)
