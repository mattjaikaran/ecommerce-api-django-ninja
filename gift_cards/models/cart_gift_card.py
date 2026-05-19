import uuid

from django.db import models

from .gift_card import GiftCard


class CartGiftCard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(
        "cart.Cart", on_delete=models.CASCADE, related_name="applied_gift_cards"
    )
    gift_card = models.ForeignKey(GiftCard, on_delete=models.CASCADE)
    amount_applied = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.gift_card.code} on cart {self.cart_id}"

    class Meta:
        verbose_name = "Cart Gift Card"
        verbose_name_plural = "Cart Gift Cards"
        ordering = ["-created_at"]
        unique_together = [("cart", "gift_card")]
