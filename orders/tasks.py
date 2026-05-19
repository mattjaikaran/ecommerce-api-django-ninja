"""Celery tasks for order processing."""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="orders",
    name="orders.tasks.send_order_confirmation_email",
)
def send_order_confirmation_email(self, order_id: str) -> None:
    """Send order confirmation email after successful payment."""
    from orders.models import Order

    try:
        order = Order.objects.select_related(
            "customer", "shipping_address", "billing_address"
        ).prefetch_related("items__product_variant__product").get(id=order_id)

        context = {
            "order": order,
            "order_items": order.items.all(),
            "customer_name": order.customer.get_full_name() or order.email,
            "frontend_url": settings.FRONTEND_URL,
        }

        html_body = render_to_string("emails/order_confirmation.html", context)
        plain_body = strip_tags(html_body)

        send_mail(
            subject=f"Order Confirmation #{order.order_number}",
            message=plain_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.email],
            html_message=html_body,
            fail_silently=False,
        )
        logger.info("order confirmation sent", extra={"order_id": order_id, "email": order.email})

    except Exception as exc:
        logger.exception("order confirmation failed", extra={"order_id": order_id})
        raise self.retry(exc=exc) from exc
