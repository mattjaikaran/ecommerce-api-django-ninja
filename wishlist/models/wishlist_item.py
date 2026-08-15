import uuid

from django.db import models

from core.models import AbstractBaseModel
from products.models import ProductVariant

from .wishlist import Wishlist


class WishlistItem(AbstractBaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wishlist = models.ForeignKey(
        Wishlist, on_delete=models.CASCADE, related_name="items"
    )
    product_variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="wishlist_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.product_variant} x{self.quantity}"

    class Meta:
        verbose_name = "Wishlist Item"
        verbose_name_plural = "Wishlist Items"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["wishlist", "product_variant"],
                name="unique_wishlist_product_variant",
            ),
        ]
        indexes = [
            models.Index(fields=["wishlist"]),
            models.Index(fields=["product_variant"]),
        ]
