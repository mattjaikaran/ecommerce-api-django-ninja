import uuid

from django.db import models

from .gift_card import GiftCard


class TransactionType(models.TextChoices):
    ISSUED = "issued", "Issued"
    REDEEMED = "redeemed", "Redeemed"
    REFUNDED = "refunded", "Refunded"
    EXPIRED = "expired", "Expired"
    VOIDED = "voided", "Voided"


class GiftCardTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gift_card = models.ForeignKey(
        GiftCard, on_delete=models.CASCADE, related_name="transactions"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    order_id = models.UUIDField(null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_type} {self.amount} for {self.gift_card.code}"

    class Meta:
        verbose_name = "Gift Card Transaction"
        verbose_name_plural = "Gift Card Transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["gift_card"]),
            models.Index(fields=["created_at"]),
        ]
