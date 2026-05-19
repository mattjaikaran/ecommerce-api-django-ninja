"""StripeWebhookEvent — idempotent log of every received Stripe event."""

import uuid

from django.db import models

from .choices import WebhookEventStatus


class StripeWebhookEvent(models.Model):
    """Persists every inbound Stripe webhook for idempotency and audit."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stripe_event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=WebhookEventStatus.choices, default=WebhookEventStatus.RECEIVED)
    payload = models.JSONField(default=dict)
    error = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.event_type} — {self.stripe_event_id} ({self.status})"

    class Meta:
        verbose_name = "Stripe Webhook Event"
        verbose_name_plural = "Stripe Webhook Events"
        indexes = [
            models.Index(fields=["stripe_event_id"]),
            models.Index(fields=["event_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["received_at"]),
        ]
