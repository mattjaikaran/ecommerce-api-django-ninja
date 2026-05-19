"""Inbound Stripe webhook handler.

Lives outside NinjaExtraAPI so it receives the raw request body (required for
signature verification) and bypasses JWT auth.
"""

import json
import logging

import stripe
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from payments.models import StripeWebhookEvent
from payments.models.choices import WebhookEventStatus

logger = logging.getLogger(__name__)

HANDLED_EVENTS = {
    "payment_intent.succeeded",
    "payment_intent.payment_failed",
    "charge.refunded",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.payment_succeeded",
    "invoice.payment_failed",
}


@csrf_exempt
@require_POST
def stripe_webhook(request) -> HttpResponse:
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        logger.warning("stripe_webhook: invalid payload")
        return JsonResponse({"error": "Invalid payload"}, status=400)
    except stripe.error.SignatureVerificationError:
        logger.warning("stripe_webhook: invalid signature")
        return JsonResponse({"error": "Invalid signature"}, status=400)

    # Idempotency check
    if StripeWebhookEvent.objects.filter(stripe_event_id=event["id"]).exists():
        return JsonResponse({"status": "already_processed"}, status=200)

    webhook_log = StripeWebhookEvent.objects.create(
        stripe_event_id=event["id"],
        event_type=event["type"],
        payload=json.loads(payload),
        status=WebhookEventStatus.RECEIVED,
    )

    if event["type"] not in HANDLED_EVENTS:
        webhook_log.status = WebhookEventStatus.IGNORED
        webhook_log.processed_at = timezone.now()
        webhook_log.save(update_fields=["status", "processed_at"])
        return JsonResponse({"status": "ignored"}, status=200)

    from payments.tasks import dispatch_stripe_event

    dispatch_stripe_event.delay(str(webhook_log.id), event["type"], event["data"])

    return JsonResponse({"status": "queued"}, status=200)
