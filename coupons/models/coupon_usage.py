import uuid

from django.db import models

from core.models import AbstractBaseModel, Customer

from .coupon import Coupon


class CouponUsage(AbstractBaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="usages")
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="coupon_usages"
    )
    # order FK added as string reference to avoid circular import
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="coupon_usages",
        null=True,
        blank=True,
    )
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.coupon.code} used by {self.customer}"

    class Meta:
        verbose_name = "Coupon Usage"
        verbose_name_plural = "Coupon Usages"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["coupon", "customer"]),
            models.Index(fields=["order"]),
        ]
