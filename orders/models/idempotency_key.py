"""Idempotency key model for replay-safe order creation."""

import uuid

from django.conf import settings
from django.db import models

from .order import Order


class IdempotencyKey(models.Model):
    """Persists a claimed idempotency key for an order creation request.

    The raw client key is never stored; only its SHA-256 hash. A unique
    constraint on (key_hash, user) makes concurrent duplicate requests
    safe: exactly one request claims the key and creates the order, and
    every later request with the same key returns the same order.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key_hash = models.CharField(max_length=64, db_index=True)
    request_hash = models.CharField(max_length=64)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="idempotency_keys",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="idempotency_keys",
        null=True,
        blank=True,
    )
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "Idempotency Key"
        verbose_name_plural = "Idempotency Keys"
        constraints = [
            models.UniqueConstraint(
                fields=["key_hash", "user"], name="unique_idempotency_key_per_user"
            ),
        ]
        indexes = [
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"IdempotencyKey {self.key_hash[:8]} for {self.user_id}"
