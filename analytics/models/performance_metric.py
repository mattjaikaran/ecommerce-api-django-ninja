import uuid

from django.db import models

from core.models import AbstractBaseModel

from .choices import MetricType, TimePeriod


class PerformanceMetric(AbstractBaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_type = models.CharField(max_length=50, choices=MetricType.choices)
    period = models.CharField(
        max_length=50, choices=TimePeriod.choices, default=TimePeriod.DAILY
    )
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    value = models.DecimalField(max_digits=12, decimal_places=4, default=0.00)
    previous_value = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )
    change_percentage = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    meta_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.value}"

    class Meta:
        verbose_name = "Performance Metric"
        verbose_name_plural = "Performance Metrics"
        ordering = ["-period_start"]
        indexes = [
            models.Index(fields=["metric_type"]),
            models.Index(fields=["period"]),
            models.Index(fields=["period_start", "period_end"]),
        ]
