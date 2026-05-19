"""Cart item model definition."""

from django.core.validators import MinValueValidator
from django.db import models

from core.models import AbstractBaseModel
from products.models import ProductVariant

from .cart import Cart


class CartItem(AbstractBaseModel):
    """Shopping cart item model for storing individual cart items."""

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product_variant.product.name}"

    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        ordering = ["-created_at"]
        indexes = [
            # Core lookup indexes
            models.Index(fields=["cart"]),
            models.Index(fields=["product_variant"]),
            # Date-based indexes
            models.Index(fields=["created_at"]),
            models.Index(fields=["updated_at"]),
            # Compound indexes for common queries
            models.Index(fields=["cart", "product_variant"]),
        ]
