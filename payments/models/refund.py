"""PaymentRefund model — records refunds against a transaction."""

from django.db import models

from core.models import AbstractBaseModel

from .choices import RefundReason, RefundStatus
from .transaction import PaymentTransaction


class PaymentRefund(AbstractBaseModel):
    transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.CASCADE,
        related_name="refunds",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=50, choices=RefundStatus.choices, default=RefundStatus.PENDING)
    reason = models.CharField(max_length=50, choices=RefundReason.choices, default=RefundReason.REQUESTED_BY_CUSTOMER)

    stripe_refund_id = models.CharField(max_length=255, blank=True)
    gateway_response = models.JSONField(default=dict)
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"Refund {self.amount} {self.currency} — {self.status}"

    class Meta:
        verbose_name = "Payment Refund"
        verbose_name_plural = "Payment Refunds"
        indexes = [
            models.Index(fields=["transaction"]),
            models.Index(fields=["status"]),
            models.Index(fields=["stripe_refund_id"]),
            models.Index(fields=["created_at"]),
        ]
