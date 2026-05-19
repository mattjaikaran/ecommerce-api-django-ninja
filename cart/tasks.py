"""Celery tasks for cart management."""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)

# Cart is "abandoned" if active, has a logged-in customer with an email,
# has items, and hasn't been updated in ABANDONED_CART_HOURS hours.
ABANDONED_CART_HOURS = 2


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    queue="cart",
    name="cart.tasks.send_abandoned_cart_emails",
)
def send_abandoned_cart_emails(self) -> None:
    """Email customers who left items in their cart without checking out."""
    from cart.models import Cart

    try:
        cutoff = timezone.now() - timedelta(hours=ABANDONED_CART_HOURS)
        abandoned = (
            Cart.objects.filter(
                is_active=True,
                customer__isnull=False,
                customer__email__isnull=False,
                updated_at__lte=cutoff,
                total_quantity__gt=0,
            )
            .select_related("customer")
            .prefetch_related("cartitem_set__product_variant__product")
        )

        sent = 0
        for cart in abandoned:
            customer = cart.customer
            email = customer.email
            if not email:
                continue

            items_lines = [
                f"- {item.product_variant.product.name} x{item.quantity} (${item.price})"
                for item in cart.cartitem_set.all()
            ]
            items_text = "\n".join(items_lines) if items_lines else "Your saved items"

            body = (
                f"Hi {customer.first_name or 'there'},\n\n"
                f"You left some items in your cart:\n\n{items_text}\n\n"
                f"Cart total: ${cart.total_price}\n\n"
                f"Complete your purchase: {settings.FRONTEND_URL}/cart\n\n"
                f"Your cart will be saved for 24 hours."
            )

            send_mail(
                subject="You left something in your cart",
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            sent += 1

        logger.info("abandoned_cart_emails_sent", extra={"count": sent})

    except Exception as exc:
        logger.exception("abandoned_cart_email_failed")
        raise self.retry(exc=exc) from exc


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    queue="cart",
    name="cart.tasks.cleanup_expired_carts",
)
def cleanup_expired_carts(self) -> None:
    """Delete carts that have passed their expiry date."""
    from cart.models import Cart

    try:
        result = Cart.objects.filter(expires_at__lt=timezone.now()).delete()
        count = result[0]
        logger.info("expired_carts_cleaned", extra={"count": count})

    except Exception as exc:
        logger.exception("cleanup_expired_carts_failed")
        raise self.retry(exc=exc) from exc
