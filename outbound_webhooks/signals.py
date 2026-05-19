import logging

logger = logging.getLogger(__name__)


def fire_webhook_event(event_type: str, payload: dict) -> None:
    from outbound_webhooks.models import WebhookDelivery, WebhookEndpoint
    from outbound_webhooks.tasks import deliver_webhook

    endpoints = WebhookEndpoint.objects.filter(is_active=True)
    for endpoint in endpoints:
        if event_type not in (endpoint.events or []):
            continue
        delivery = WebhookDelivery.objects.create(
            endpoint=endpoint,
            event_type=event_type,
            payload=payload,
        )
        deliver_webhook.delay(str(delivery.id))
        logger.info("fire_webhook_event: queued %s for %s", event_type, endpoint.url)
