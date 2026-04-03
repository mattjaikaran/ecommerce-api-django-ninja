import uuid

from django.db import models

from core.models import AbstractBaseModel, Customer

from .choices import TimePeriod


class CustomerAnalytics(AbstractBaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="analytics"
    )
    period = models.CharField(
        max_length=50, choices=TimePeriod.choices, default=TimePeriod.MONTHLY
    )
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    total_orders = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    average_order_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    total_returns = models.PositiveIntegerField(default=0)
    lifetime_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    meta_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Customer {self.customer_id} - {self.period_start:%Y-%m-%d}"

    class Meta:
        verbose_name = "Customer Analytics"
        verbose_name_plural = "Customer Analytics"
        ordering = ["-period_start"]
        indexes = [
            models.Index(fields=["customer"]),
            models.Index(fields=["period"]),
            models.Index(fields=["period_start", "period_end"]),
        ]
