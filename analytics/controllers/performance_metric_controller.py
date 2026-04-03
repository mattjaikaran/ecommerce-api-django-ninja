import logging

from django.shortcuts import get_object_or_404
from ninja.pagination import paginate
from ninja_extra import (
    api_controller,
    http_get,
)
from ninja_extra.permissions import IsAuthenticated

from api.decorators import handle_exceptions, log_api_call

from ..models import MetricType, PerformanceMetric
from ..schemas import PerformanceMetricSchema

logger = logging.getLogger(__name__)


@api_controller("/analytics/metrics", tags=["Analytics - Metrics"])
class PerformanceMetricController:
    permission_classes = [IsAuthenticated]

    @http_get("", response={200: list[PerformanceMetricSchema]})
    @handle_exceptions
    @log_api_call()
    @paginate
    def list_metrics(
        self, request, metric_type: str | None = None, period: str | None = None
    ):
        """Get paginated list of performance metrics."""
        qs = PerformanceMetric.objects.order_by("-period_start")
        if metric_type:
            qs = qs.filter(metric_type=metric_type)
        if period:
            qs = qs.filter(period=period)
        return qs

    @http_get("/{metric_id}", response={200: PerformanceMetricSchema})
    @handle_exceptions
    @log_api_call()
    def get_metric(self, request, metric_id: str):
        """Get a specific performance metric."""
        metric = get_object_or_404(PerformanceMetric, id=metric_id)
        return 200, metric

    @http_get("/types", response={200: list[dict]})
    @handle_exceptions
    @log_api_call()
    def list_metric_types(self, request):
        """Get available metric types."""
        return 200, [
            {"value": choice[0], "label": choice[1]} for choice in MetricType.choices
        ]
