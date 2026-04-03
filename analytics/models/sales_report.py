import uuid

from django.core.validators import MinValueValidator
from django.db import models

from core.models import AbstractBaseModel

from .choices import ReportType, TimePeriod


class SalesReport(AbstractBaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(
        max_length=50, choices=ReportType.choices, default=ReportType.SALES
    )
    period = models.CharField(
        max_length=50, choices=TimePeriod.choices, default=TimePeriod.DAILY
    )
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    total_revenue = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0)]
    )
    total_orders = models.PositiveIntegerField(default=0)
    total_items_sold = models.PositiveIntegerField(default=0)
    average_order_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)]
    )
    total_discounts = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)]
    )
    total_refunds = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)]
    )
    total_tax = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)]
    )
    total_shipping = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)]
    )
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    new_customers = models.PositiveIntegerField(default=0)
    returning_customers = models.PositiveIntegerField(default=0)
    meta_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        start = self.period_start.strftime("%Y-%m-%d")
        end = self.period_end.strftime("%Y-%m-%d")
        return f"{self.get_report_type_display()} - {start} to {end}"

    class Meta:
        verbose_name = "Sales Report"
        verbose_name_plural = "Sales Reports"
        ordering = ["-period_start"]
        indexes = [
            models.Index(fields=["report_type"]),
            models.Index(fields=["period"]),
            models.Index(fields=["period_start", "period_end"]),
        ]
