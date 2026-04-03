import logging
from datetime import datetime, timedelta, timezone

from django.db import models, transaction
from django.shortcuts import get_object_or_404
from ninja.pagination import paginate
from ninja_extra import (
    api_controller,
    http_get,
    http_post,
)
from ninja_extra.permissions import IsAuthenticated

from api.decorators import handle_exceptions, log_api_call
from api.exceptions import ValidationError
from orders.models import Order, OrderStatus, Refund

from ..models import ReportType, SalesReport, TimePeriod
from ..schemas import SalesReportSchema

logger = logging.getLogger(__name__)


@api_controller("/analytics/sales", tags=["Analytics - Sales"])
class SalesReportController:
    permission_classes = [IsAuthenticated]

    @http_get("", response={200: list[SalesReportSchema]})
    @handle_exceptions
    @log_api_call()
    @paginate
    def list_reports(
        self, request, report_type: str | None = None, period: str | None = None
    ):
        """Get paginated list of sales reports."""
        qs = SalesReport.objects.order_by("-period_start")
        if report_type:
            qs = qs.filter(report_type=report_type)
        if period:
            qs = qs.filter(period=period)
        return qs

    @http_get("/{report_id}", response={200: SalesReportSchema})
    @handle_exceptions
    @log_api_call()
    def get_report(self, request, report_id: str):
        """Get a specific sales report."""
        report = get_object_or_404(SalesReport, id=report_id)
        return 200, report

    @http_post("/generate", response={201: SalesReportSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def generate_report(
        self,
        request,
        report_type: str = ReportType.SALES,
        period: str = TimePeriod.DAILY,
    ):
        """Generate a sales report for the current period."""
        now = datetime.now(tz=timezone.utc)

        if period == TimePeriod.DAILY:
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
        elif period == TimePeriod.WEEKLY:
            period_start = now - timedelta(days=now.weekday())
            period_start = period_start.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            period_end = period_start + timedelta(weeks=1)
        elif period == TimePeriod.MONTHLY:
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                period_end = period_start.replace(year=now.year + 1, month=1)
            else:
                period_end = period_start.replace(month=now.month + 1)
        else:
            raise ValidationError(f"Unsupported period: {period}")

        # Aggregate order data
        completed_orders = Order.objects.filter(
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            created_at__gte=period_start,
            created_at__lt=period_end,
        )

        aggregates = completed_orders.aggregate(
            total_revenue=models.Sum("total"),
            total_orders=models.Count("id"),
            total_items=models.Sum("subtotal"),
            avg_order_value=models.Avg("total"),
            total_discounts=models.Sum("discount_amount"),
            total_tax=models.Sum("tax_amount"),
            total_shipping=models.Sum("shipping_amount"),
        )

        total_refunds = (
            Refund.objects.filter(
                created_at__gte=period_start,
                created_at__lt=period_end,
                status="completed",
            ).aggregate(total=models.Sum("amount"))["total"]
            or 0
        )

        total_revenue = aggregates["total_revenue"] or 0
        net_revenue = total_revenue - total_refunds

        report = SalesReport.objects.create(
            report_type=report_type,
            period=period,
            period_start=period_start,
            period_end=period_end,
            total_revenue=total_revenue,
            total_orders=aggregates["total_orders"] or 0,
            total_items_sold=0,
            average_order_value=aggregates["avg_order_value"] or 0,
            total_discounts=aggregates["total_discounts"] or 0,
            total_refunds=total_refunds,
            total_tax=aggregates["total_tax"] or 0,
            total_shipping=aggregates["total_shipping"] or 0,
            net_revenue=net_revenue,
            created_by=request.user,
        )

        return 201, report

    @http_get("/summary", response={200: dict})
    @handle_exceptions
    @log_api_call()
    def get_summary(self, request):
        """Get a quick summary of recent sales metrics."""
        now = datetime.now(tz=timezone.utc)
        thirty_days_ago = now - timedelta(days=30)

        orders = Order.objects.filter(
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            created_at__gte=thirty_days_ago,
        )

        aggregates = orders.aggregate(
            total_revenue=models.Sum("total"),
            total_orders=models.Count("id"),
            avg_order_value=models.Avg("total"),
        )

        return 200, {
            "period": "last_30_days",
            "total_revenue": str(aggregates["total_revenue"] or 0),
            "total_orders": aggregates["total_orders"] or 0,
            "average_order_value": str(aggregates["avg_order_value"] or 0),
        }
