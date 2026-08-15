import uuid

from django.db import models

from core.models import AbstractBaseModel, Customer


class Wishlist(AbstractBaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.OneToOneField(
        Customer, on_delete=models.CASCADE, related_name="wishlist"
    )
    name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self) -> str:
        return f"Wishlist for {self.customer}"

    class Meta:
        verbose_name = "Wishlist"
        verbose_name_plural = "Wishlists"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer"]),
        ]
