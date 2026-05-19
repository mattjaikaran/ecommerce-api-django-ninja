"""Celery tasks for async Stripe event processing."""

import logging

from celery import shared_task
from django.utils import timezone

from payments.models import StripeWebhookEvent
from payments.models.choices import WebhookEventStatus

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="payments",
    name="payments.tasks.dispatch_stripe_event",
)
def dispatch_stripe_event(self, webhook_log_id: str, event_type: str, event_data: dict) -> None:
    """Route a Stripe webhook event to the appropriate handler."""
    from payments.services import PaymentService

    try:
        handlers = {
            "payment_intent.succeeded": PaymentService.handle_payment_intent_succeeded,
            "payment_intent.payment_failed": PaymentService.handle_payment_intent_failed,
            "charge.refunded": PaymentService.handle_charge_refunded,
        }

        handler = handlers.get(event_type)
        if handler:
            handler(event_data)

        StripeWebhookEvent.objects.filter(id=webhook_log_id).update(
            status=WebhookEventStatus.PROCESSED,
            processed_at=timezone.now(),
        )
        logger.info("stripe event processed: %s %s", event_type, webhook_log_id)

    except Exception as exc:
        StripeWebhookEvent.objects.filter(id=webhook_log_id).update(
            status=WebhookEventStatus.FAILED,
            error=str(exc),
            processed_at=timezone.now(),
        )
        logger.exception("stripe event failed: %s %s", event_type, webhook_log_id)
        raise self.retry(exc=exc)
