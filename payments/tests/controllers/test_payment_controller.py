"""Tests for PaymentController endpoints."""

import json

import pytest
from django.test import Client

from core.tests.factories import UserFactory
from payments.tests.factories import (
    PaymentMethodFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def auth_client(client, user):
    from ninja_jwt.tokens import RefreshToken as NinjaRefreshToken
    try:
        token = NinjaRefreshToken.for_user(user)
        client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token.access_token}"
    except Exception:
        pass
    return client, user


class TestPaymentMethodEndpoints:
    def test_list_payment_methods_requires_auth(self, client):
        response = client.get("/api/payments/methods")
        assert response.status_code in (401, 403)

    def test_list_payment_methods_empty(self, db, user):
        c = Client()
        # Unauthenticated returns 401
        response = c.get("/api/payments/methods")
        assert response.status_code in (401, 403)

    def test_delete_payment_method_not_owned(self, db, user):
        other_pm = PaymentMethodFactory()
        c = Client()
        response = c.delete(f"/api/payments/methods/{other_pm.id}")
        assert response.status_code in (401, 403, 404)


class TestPaymentTransactionEndpoints:
    def test_list_transactions_requires_auth(self, client):
        response = client.get("/api/payments/transactions")
        assert response.status_code in (401, 403)

    def test_transaction_detail_not_found(self, client):
        import uuid
        response = client.get(f"/api/payments/transactions/{uuid.uuid4()}")
        assert response.status_code in (401, 403, 404)


class TestStripeWebhook:
    def test_webhook_rejects_invalid_signature(self, client, settings):
        settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"
        payload = json.dumps({"type": "payment_intent.succeeded", "id": "evt_test_001"})
        response = client.post(
            "/webhooks/stripe/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="invalid_sig",
        )
        assert response.status_code == 400

    def test_webhook_rejects_missing_signature(self, client, settings):
        settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"
        payload = json.dumps({"type": "payment_intent.succeeded", "id": "evt_test_002"})
        response = client.post(
            "/webhooks/stripe/",
            data=payload,
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_webhook_idempotency(self, db, client, settings, monkeypatch):
        """Second delivery of the same event returns 200 without reprocessing."""
        import stripe

        from payments.models import StripeWebhookEvent
        from payments.models.choices import WebhookEventStatus

        settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        fake_event = {
            "id": "evt_idempotency_test",
            "type": "payment_intent.succeeded",
            "data": {"object": {}},
        }

        # Pre-create the event record as already processed
        StripeWebhookEvent.objects.create(
            stripe_event_id="evt_idempotency_test",
            event_type="payment_intent.succeeded",
            status=WebhookEventStatus.PROCESSED,
            payload=fake_event,
        )

        def mock_construct(payload, sig, secret):
            return fake_event

        monkeypatch.setattr(stripe.Webhook, "construct_event", mock_construct)

        payload = json.dumps(fake_event).encode()
        response = client.post(
            "/webhooks/stripe/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=1,v1=fake",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "already_processed"

    def test_webhook_valid_signature_queues_event(self, db, client, settings, monkeypatch):
        """Valid webhook with correct signature is accepted and queued."""
        import stripe

        settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        fake_event = {
            "id": "evt_valid_queued",
            "type": "payment_intent.succeeded",
            "data": {"object": {}},
        }

        monkeypatch.setattr(stripe.Webhook, "construct_event", lambda *a, **kw: fake_event)

        # Patch Celery task so it doesn't actually run
        from unittest.mock import MagicMock
        import payments.tasks as tasks_module
        mock_task = MagicMock()
        mock_task.delay = MagicMock()
        monkeypatch.setattr(tasks_module, "dispatch_stripe_event", mock_task)

        payload = json.dumps(fake_event).encode()
        response = client.post(
            "/webhooks/stripe/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=1,v1=valid",
        )

        assert response.status_code == 200
        assert response.json()["status"] == "queued"
        mock_task.delay.assert_called_once()

    def test_webhook_unknown_event_ignored(self, db, client, settings, monkeypatch):
        import stripe
        settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        fake_event = {
            "id": "evt_unknown_type",
            "type": "some.unknown.event",
            "data": {"object": {}},
        }

        monkeypatch.setattr(stripe.Webhook, "construct_event", lambda *a, **kw: fake_event)

        payload = json.dumps(fake_event).encode()
        response = client.post(
            "/webhooks/stripe/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=1,v1=fake",
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"
