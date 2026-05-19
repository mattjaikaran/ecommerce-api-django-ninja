import logging

from django.shortcuts import get_object_or_404

from outbound_webhooks.models import WebhookDelivery, WebhookEndpoint

logger = logging.getLogger(__name__)


class WebhookService:
    @staticmethod
    def create_endpoint(payload) -> WebhookEndpoint:
        return WebhookEndpoint.objects.create(
            url=payload.url,
            description=payload.description,
            events=payload.events,
            is_active=payload.is_active,
        )

    @staticmethod
    def update_endpoint(endpoint: WebhookEndpoint, payload) -> WebhookEndpoint:
        if payload.url is not None:
            endpoint.url = payload.url
        if payload.description is not None:
            endpoint.description = payload.description
        if payload.events is not None:
            endpoint.events = payload.events
        if payload.is_active is not None:
            endpoint.is_active = payload.is_active
        endpoint.save()
        return endpoint

    @staticmethod
    def delete_endpoint(endpoint: WebhookEndpoint) -> None:
        endpoint.delete()

    @staticmethod
    def list_deliveries(endpoint_id: str):
        return WebhookDelivery.objects.filter(endpoint_id=endpoint_id).order_by("-created_at")

    @staticmethod
    def redeliver(delivery_id: str) -> WebhookDelivery:
        from outbound_webhooks.tasks import deliver_webhook

        delivery = get_object_or_404(WebhookDelivery, id=delivery_id)
        deliver_webhook.delay(str(delivery.id))
        logger.info("redeliver: queued delivery %s", delivery_id)
        return delivery
