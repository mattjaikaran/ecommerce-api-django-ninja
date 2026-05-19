"""Celery tasks for analytics rollup."""

import logging
from datetime import timedelta
from decimal import Decimal

from celery import shared_task
from django.db.models import Count, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=300,
    queue="core",
    name="analytics.tasks.rollup_daily_sales",
)
def rollup_daily_sales(self) -> None:
    """Aggregate yesterday's orders into a SalesReport row."""
    from analytics.models import SalesReport, TimePeriod
    from orders.models import Order, OrderStatus, PaymentStatus

    try:
        now = timezone.now()
        period_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_start = period_end - timedelta(days=1)

        # Skip if a report already exists for this period
        if SalesReport.objects.filter(period=TimePeriod.DAILY, period_start=period_start).exists():
            logger.info("daily_sales_rollup_skipped: report already exists", extra={"date": period_start.date().isoformat()})
            return

        completed_orders = Order.objects.filter(
            created_at__gte=period_start,
            created_at__lt=period_end,
            payment_status=PaymentStatus.PAID,
        )

        agg = completed_orders.aggregate(
            total_revenue=Sum("total"),
            total_orders=Count("id"),
            total_items=Sum("items__quantity"),
            total_discounts=Sum("discount_amount"),
            total_tax=Sum("tax_amount"),
            total_shipping=Sum("shipping_amount"),
        )

        total_revenue = agg["total_revenue"] or Decimal("0.00")
        total_orders = agg["total_orders"] or 0
        avg_order_value = (total_revenue / total_orders) if total_orders else Decimal("0.00")

        refunded = Order.objects.filter(
            created_at__gte=period_start,
            created_at__lt=period_end,
            status=OrderStatus.REFUNDED,
        ).aggregate(total=Sum("total"))["total"] or Decimal("0.00")

        # New vs returning customers
        customer_ids = set(completed_orders.values_list("customer_id", flat=True))
        new_customers = sum(
            1
            for cid in customer_ids
            if not Order.objects.filter(
                customer_id=cid,
                created_at__lt=period_start,
                payment_status=PaymentStatus.PAID,
            ).exists()
        )
        returning_customers = len(customer_ids) - new_customers

        SalesReport.objects.create(
            period=TimePeriod.DAILY,
            period_start=period_start,
            period_end=period_end,
            total_revenue=total_revenue,
            total_orders=total_orders,
            total_items_sold=agg["total_items"] or 0,
            average_order_value=avg_order_value,
            total_discounts=agg["total_discounts"] or Decimal("0.00"),
            total_refunds=refunded,
            total_tax=agg["total_tax"] or Decimal("0.00"),
            total_shipping=agg["total_shipping"] or Decimal("0.00"),
            net_revenue=total_revenue - refunded,
            new_customers=new_customers,
            returning_customers=returning_customers,
        )

        logger.info(
            "daily_sales_rollup_complete",
            extra={
                "date": period_start.date().isoformat(),
                "orders": total_orders,
                "revenue": str(total_revenue),
            },
        )

    except Exception as exc:
        logger.exception("daily_sales_rollup_failed")
        raise self.retry(exc=exc) from exc


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=300,
    queue="core",
    name="analytics.tasks.rollup_product_analytics",
)
def rollup_product_analytics(self) -> None:
    """Aggregate yesterday's per-product sales into ProductAnalytics rows."""
    from analytics.models import ProductAnalytics, TimePeriod
    from orders.models import OrderLineItem, PaymentStatus

    try:
        now = timezone.now()
        period_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_start = period_end - timedelta(days=1)

        rows = (
            OrderLineItem.objects.filter(
                order__created_at__gte=period_start,
                order__created_at__lt=period_end,
                order__payment_status=PaymentStatus.PAID,
            )
            .values("product_variant__product_id")
            .annotate(
                units_sold=Sum("quantity"),
                revenue=Sum("subtotal"),
            )
        )

        created = 0
        for row in rows:
            product_id = row["product_variant__product_id"]
            if ProductAnalytics.objects.filter(
                product_id=product_id,
                period=TimePeriod.DAILY,
                period_start=period_start,
            ).exists():
                continue

            ProductAnalytics.objects.create(
                product_id=product_id,
                period=TimePeriod.DAILY,
                period_start=period_start,
                period_end=period_end,
                units_sold=row["units_sold"] or 0,
                revenue=row["revenue"] or Decimal("0.00"),
            )
            created += 1

        logger.info("product_analytics_rollup_complete", extra={"products_updated": created})

    except Exception as exc:
        logger.exception("product_analytics_rollup_failed")
        raise self.retry(exc=exc) from exc
