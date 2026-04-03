import uuid

from django.db import models

from core.models import AbstractBaseModel
from products.models import Product

from .choices import TimePeriod


class ProductAnalytics(AbstractBaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="analytics"
    )
    period = models.CharField(
        max_length=50, choices=TimePeriod.choices, default=TimePeriod.DAILY
    )
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    units_sold = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    views = models.PositiveIntegerField(default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    returns = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True
    )
    meta_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.period_start:%Y-%m-%d}"

    class Meta:
        verbose_name = "Product Analytics"
        verbose_name_plural = "Product Analytics"
        ordering = ["-period_start"]
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["period"]),
            models.Index(fields=["period_start", "period_end"]),
        ]
