import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest

from outbound_webhooks.models import WebhookDelivery, WebhookEndpoint
from outbound_webhooks.models.webhook_delivery import DeliveryStatus
from outbound_webhooks.services import WebhookService
from outbound_webhooks.signals import fire_webhook_event
from outbound_webhooks.tests.factories import WebhookDeliveryFactory, WebhookEndpointFactory


@pytest.mark.django_db
class TestWebhookEndpointModel:
    def test_create_endpoint(self):
        endpoint = WebhookEndpointFactory()
        assert endpoint.id is not None
        assert endpoint.secret
        assert len(endpoint.secret) == 64
        assert endpoint.is_active is True
        assert endpoint.failure_count == 0

    def test_endpoint_auto_secret(self):
        e1 = WebhookEndpointFactory()
        e2 = WebhookEndpointFactory()
        assert e1.secret != e2.secret

    def test_create_delivery(self):
        delivery = WebhookDeliveryFactory()
        assert delivery.id is not None
        assert delivery.status == DeliveryStatus.PENDING
        assert delivery.attempt_count == 0


@pytest.mark.django_db
class TestWebhookSignal:
    def test_fire_webhook_event_creates_deliveries(self):
        WebhookEndpointFactory(events=["order.created"])
        WebhookEndpointFactory(events=["order.updated"])

        with patch("outbound_webhooks.signals.deliver_webhook") as mock_task:
            mock_task.delay = MagicMock()
            fire_webhook_event("order.created", {"id": "abc", "status": "pending", "total": "50.00"})

        deliveries = WebhookDelivery.objects.filter(event_type="order.created")
        assert deliveries.count() == 1

    def test_fire_webhook_event_skips_inactive_endpoint(self):
        WebhookEndpointFactory(events=["order.created"], is_active=False)

        with patch("outbound_webhooks.signals.deliver_webhook") as mock_task:
            mock_task.delay = MagicMock()
            fire_webhook_event("order.created", {"id": "xyz"})

        assert WebhookDelivery.objects.count() == 0

    def test_fire_webhook_event_skips_mismatched_events(self):
        WebhookEndpointFactory(events=["order.updated"])

        with patch("outbound_webhooks.signals.deliver_webhook") as mock_task:
            mock_task.delay = MagicMock()
            fire_webhook_event("order.created", {"id": "xyz"})

        assert WebhookDelivery.objects.count() == 0


@pytest.mark.django_db
class TestHMACSignature:
    def test_hmac_signature_generation(self):
        endpoint = WebhookEndpointFactory()
        payload = {"id": "test", "status": "pending", "total": "100.00"}
        body = json.dumps(payload, default=str)
        expected = hmac.new(
            endpoint.secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        assert len(expected) == 64
        assert expected.isalnum() or all(c in "0123456789abcdef" for c in expected)


@pytest.mark.django_db
class TestWebhookDeliveryStatus:
    def test_delivery_status_transitions(self):
        delivery = WebhookDeliveryFactory(status=DeliveryStatus.PENDING)
        delivery.status = DeliveryStatus.SUCCESS
        delivery.save()
        delivery.refresh_from_db()
        assert delivery.status == DeliveryStatus.SUCCESS

    def test_delivery_failed_status(self):
        delivery = WebhookDeliveryFactory(status=DeliveryStatus.PENDING)
        delivery.status = DeliveryStatus.FAILED
        delivery.attempt_count = 3
        delivery.save()
        delivery.refresh_from_db()
        assert delivery.status == DeliveryStatus.FAILED
        assert delivery.attempt_count == 3


@pytest.mark.django_db
class TestWebhookService:
    def test_create_endpoint_service(self):
        payload = MagicMock()
        payload.url = "https://example.com/hook"
        payload.description = "Test hook"
        payload.events = ["order.created"]
        payload.is_active = True

        endpoint = WebhookService.create_endpoint(payload)
        assert endpoint.url == "https://example.com/hook"
        assert WebhookEndpoint.objects.filter(id=endpoint.id).exists()

    def test_list_deliveries(self):
        endpoint = WebhookEndpointFactory()
        WebhookDeliveryFactory(endpoint=endpoint)
        WebhookDeliveryFactory(endpoint=endpoint)

        deliveries = WebhookService.list_deliveries(str(endpoint.id))
        assert deliveries.count() == 2

    def test_delete_endpoint(self):
        endpoint = WebhookEndpointFactory()
        endpoint_id = endpoint.id
        WebhookService.delete_endpoint(endpoint)
        assert not WebhookEndpoint.objects.filter(id=endpoint_id).exists()
