from decimal import Decimal

from django.db import models

from core.models import AbstractBaseModel, Customer


class LoyaltyAccount(AbstractBaseModel):
    """Customer loyalty account holding a redeemable points balance."""

    customer = models.OneToOneField(
        Customer, on_delete=models.CASCADE, related_name="loyalty_account"
    )
    balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    lifetime_points = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )

    def __str__(self) -> str:
        return f"Loyalty account for {self.customer}"

    class Meta:
        verbose_name = "Loyalty Account"
        verbose_name_plural = "Loyalty Accounts"
        ordering = ["-created_at"]
