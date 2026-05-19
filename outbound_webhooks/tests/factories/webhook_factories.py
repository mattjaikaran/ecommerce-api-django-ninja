import factory

from outbound_webhooks.models import WebhookDelivery, WebhookEndpoint
from outbound_webhooks.models.webhook_delivery import DeliveryStatus


class WebhookEndpointFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WebhookEndpoint

    url = factory.Sequence(lambda n: f"https://example.com/webhook/{n}")
    description = factory.Faker("sentence")
    events = ["order.created", "order.updated"]
    is_active = True
    failure_count = 0


class WebhookDeliveryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WebhookDelivery

    endpoint = factory.SubFactory(WebhookEndpointFactory)
    event_type = "order.created"
    payload = {"id": "test-id", "status": "pending", "total": "100.00"}
    status = DeliveryStatus.PENDING
    attempt_count = 0
