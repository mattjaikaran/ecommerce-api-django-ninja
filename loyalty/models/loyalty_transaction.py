from django.db import models
from django.db.models import Q

from core.models import AbstractBaseModel
from orders.models import Order

from .choices import LoyaltyReason
from .loyalty_account import LoyaltyAccount


class LoyaltyTransaction(AbstractBaseModel):
    """Signed ledger entry on a loyalty account (earn/redeem/adjust)."""

    account = models.ForeignKey(
        LoyaltyAccount, on_delete=models.CASCADE, related_name="transactions"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    order = models.ForeignKey(
        Order,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="loyalty_transactions",
    )
    reason = models.CharField(max_length=20, choices=LoyaltyReason.choices)
    reference = models.CharField(max_length=255, blank=True, default="")

    def __str__(self) -> str:
        return f"{self.reason} {self.amount} for account {self.account_id}"

    class Meta:
        verbose_name = "Loyalty Transaction"
        verbose_name_plural = "Loyalty Transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["account"]),
            models.Index(fields=["created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["account", "order"],
                condition=Q(reason="earn"),
                name="unique_earn_per_order",
            ),
        ]
