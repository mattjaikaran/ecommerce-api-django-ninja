import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import AbstractBaseModel, Customer, CustomerGroup

from .choices import DiscountType


class Coupon(AbstractBaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    discount_type = models.CharField(
        max_length=20, choices=DiscountType.choices, default=DiscountType.PERCENTAGE
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Percentage (0-100) or fixed amount depending on discount_type",
    )
    max_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Cap for percentage discounts",
    )
    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    usage_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total number of times this coupon can be used across all customers",
    )
    usage_limit_per_customer = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of times a single customer can use this coupon",
    )
    used_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    customer_group = models.ForeignKey(
        CustomerGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coupons",
        help_text="Restrict to a specific customer group; null means all customers",
    )
    restricted_customers = models.ManyToManyField(
        Customer,
        blank=True,
        related_name="restricted_coupons",
        help_text="Restrict to specific customers; empty means no per-customer restriction",
    )

    def __str__(self) -> str:
        return self.code

    class Meta:
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["valid_from", "valid_to"]),
        ]
