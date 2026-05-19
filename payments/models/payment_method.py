"""PaymentMethod model — stores customer payment instruments."""

from django.db import models

from core.models import AbstractBaseModel, Customer

from .choices import PaymentGateway, PaymentMethodType


class PaymentMethod(AbstractBaseModel):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="payment_methods",
        null=True,
        blank=True,
    )
    type = models.CharField(max_length=50, choices=PaymentMethodType.choices, default=PaymentMethodType.CARD)
    provider = models.CharField(max_length=50, choices=PaymentGateway.choices, default=PaymentGateway.STRIPE)
    is_default = models.BooleanField(default=False)

    # Stripe references
    stripe_payment_method_id = models.CharField(max_length=255, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True)

    # Card display metadata (non-sensitive, safe to store)
    last_four = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=50, blank=True)  # visa, mastercard, amex…
    expiry_month = models.PositiveSmallIntegerField(null=True, blank=True)
    expiry_year = models.PositiveSmallIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.get_card_brand_display()} •••• {self.last_four}"

    def get_card_brand_display(self) -> str:
        return self.card_brand.title() if self.card_brand else self.type

    class Meta:
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"
        indexes = [
            models.Index(fields=["customer"]),
            models.Index(fields=["stripe_payment_method_id"]),
            models.Index(fields=["stripe_customer_id"]),
            models.Index(fields=["is_default"]),
            models.Index(fields=["provider"]),
        ]
