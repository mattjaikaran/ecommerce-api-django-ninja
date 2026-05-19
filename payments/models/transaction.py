"""PaymentTransaction model — records each charge attempt against an order."""

from django.db import models

from core.models import AbstractBaseModel
from orders.models import Order

from .choices import PaymentGateway, PaymentStatus
from .payment_method import PaymentMethod


class PaymentTransaction(AbstractBaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payment_transactions")
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    gateway = models.CharField(max_length=50, choices=PaymentGateway.choices, default=PaymentGateway.STRIPE)
    status = models.CharField(max_length=50, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Stripe identifiers
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True)

    # Full gateway response for auditability
    gateway_response = models.JSONField(default=dict)

    error_code = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.order.order_number} — {self.amount} {self.currency} ({self.status})"

    class Meta:
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["status"]),
            models.Index(fields=["stripe_payment_intent_id"]),
            models.Index(fields=["stripe_charge_id"]),
            models.Index(fields=["gateway"]),
            models.Index(fields=["created_at"]),
        ]
