"""Celery tasks for loyalty point processing."""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="loyalty",
    name="loyalty.tasks.credit_order_points",
)
def credit_order_points(self, order_id: str) -> None:
    """Credit loyalty points to the customer after an order completes."""
    from loyalty.models import LoyaltyReason, LoyaltyTransaction
    from loyalty.services import LoyaltyService
    from orders.models import Order

    try:
        order = Order.objects.select_related("customer").get(id=order_id)
        if LoyaltyTransaction.objects.filter(
            reference=f"order:{order_id}", reason=LoyaltyReason.EARN
        ).exists():
            logger.info("loyalty points already credited", extra={"order_id": order_id})
            return
        LoyaltyService.earn_points(order.customer, order, order.total)
        logger.info("loyalty points credited", extra={"order_id": order_id})
    except Exception as exc:
        logger.exception("loyalty points credit failed", extra={"order_id": order_id})
        raise self.retry(exc=exc) from exc
