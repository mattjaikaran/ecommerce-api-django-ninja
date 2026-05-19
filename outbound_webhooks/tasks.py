import hashlib
import hmac
import json
import logging

import requests
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    queue="webhooks",
    name="outbound_webhooks.tasks.deliver_webhook",
)
def deliver_webhook(self, delivery_id: str) -> None:
    from outbound_webhooks.models import WebhookDelivery
    from outbound_webhooks.models.webhook_delivery import DeliveryStatus

    try:
        delivery = WebhookDelivery.objects.select_related("endpoint").get(id=delivery_id)
    except WebhookDelivery.DoesNotExist:
        logger.error("deliver_webhook: delivery %s not found", delivery_id)
        return

    endpoint = delivery.endpoint
    body = json.dumps(delivery.payload, default=str)
    signature = hmac.new(
        endpoint.secret.encode(),
        body.encode(),
        hashlib.sha256,
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": f"sha256={signature}",
        "X-Webhook-Event": delivery.event_type,
        "X-Webhook-ID": str(delivery.id),
    }

    try:
        response = requests.post(
            endpoint.url,
            data=body,
            headers=headers,
            timeout=10,
        )
        delivery.attempt_count += 1
        delivery.response_status_code = response.status_code
        delivery.response_body = response.text[:4000]

        if response.ok:
            delivery.status = DeliveryStatus.SUCCESS
            delivery.delivered_at = timezone.now()
            delivery.save()
            endpoint.failure_count = 0
            endpoint.last_success_at = timezone.now()
            endpoint.save(update_fields=["failure_count", "last_success_at"])
            logger.info("deliver_webhook: success %s -> %s", delivery.event_type, endpoint.url)
        else:
            delivery.save()
            endpoint.failure_count += 1
            endpoint.save(update_fields=["failure_count"])
            logger.warning(
                "deliver_webhook: non-2xx %s for %s", response.status_code, delivery_id
            )
            if delivery.attempt_count < 3:
                raise self.retry(countdown=60 * (2 ** delivery.attempt_count), max_retries=3)
            delivery.status = DeliveryStatus.FAILED
            delivery.save(update_fields=["status"])

    except requests.RequestException as exc:
        delivery.attempt_count += 1
        delivery.save(update_fields=["attempt_count"])
        endpoint.failure_count += 1
        endpoint.save(update_fields=["failure_count"])
        logger.exception("deliver_webhook: request error for %s", delivery_id)
        if delivery.attempt_count < 3:
            raise self.retry(exc=exc, countdown=60 * (2 ** delivery.attempt_count), max_retries=3)
        delivery.status = DeliveryStatus.FAILED
        delivery.save(update_fields=["status"])
