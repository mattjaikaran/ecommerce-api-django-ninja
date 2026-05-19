"""Celery tasks for product management."""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import F

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    queue="products",
    name="products.tasks.send_low_stock_alerts",
)
def send_low_stock_alerts(self) -> None:
    """Find variants below their low_stock_threshold and email staff."""
    from products.models import ProductVariant

    try:
        low_stock = list(
            ProductVariant.objects.filter(
                inventory_quantity__lte=F("low_stock_threshold"),
                inventory_quantity__gt=0,
                is_active=True,
            )
            .select_related("product")
            .values("id", "sku", "inventory_quantity", "low_stock_threshold", "product__name")
        )

        if not low_stock:
            logger.info("low_stock_check: no variants below threshold")
            return

        lines = [
            f"- {item['product__name']} (SKU: {item['sku']}): "
            f"{item['inventory_quantity']} remaining (threshold: {item['low_stock_threshold']})"
            for item in low_stock
        ]
        body = "The following products are running low on stock:\n\n" + "\n".join(lines)

        admin_email = getattr(settings, "ADMIN_EMAIL", settings.DEFAULT_FROM_EMAIL)
        send_mail(
            subject=f"[Low Stock Alert] {len(low_stock)} variant(s) need restocking",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=False,
        )
        logger.info("low_stock_alert_sent", extra={"count": len(low_stock)})

    except Exception as exc:
        logger.exception("low_stock_alert_failed")
        raise self.retry(exc=exc) from exc


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    queue="products",
    name="products.tasks.send_out_of_stock_alerts",
)
def send_out_of_stock_alerts(self) -> None:
    """Find variants that just hit zero inventory and notify staff."""
    from products.models import ProductVariant

    try:
        out_of_stock = list(
            ProductVariant.objects.filter(inventory_quantity=0, is_active=True)
            .select_related("product")
            .values("id", "sku", "product__name")
        )

        if not out_of_stock:
            return

        lines = [
            f"- {item['product__name']} (SKU: {item['sku']}): OUT OF STOCK"
            for item in out_of_stock
        ]
        body = "The following products are out of stock:\n\n" + "\n".join(lines)

        admin_email = getattr(settings, "ADMIN_EMAIL", settings.DEFAULT_FROM_EMAIL)
        send_mail(
            subject=f"[Out of Stock] {len(out_of_stock)} variant(s) need immediate restocking",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=False,
        )
        logger.info("out_of_stock_alert_sent", extra={"count": len(out_of_stock)})

    except Exception as exc:
        logger.exception("out_of_stock_alert_failed")
        raise self.retry(exc=exc) from exc
