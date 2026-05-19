import logging
from datetime import datetime, timezone as dt_timezone

import stripe
from django.conf import settings
from django.utils import timezone

from subscriptions.models import CustomerSubscription, SubscriptionPlan
from subscriptions.models.customer_subscription import SubscriptionStatus

logger = logging.getLogger(__name__)


class SubscriptionService:
    @staticmethod
    def create_checkout_session(customer, plan: SubscriptionPlan) -> str:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
            success_url=f"{settings.FRONTEND_URL}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/subscription/cancel",
            customer_email=customer.email if hasattr(customer, "email") else None,
            metadata={"customer_id": str(customer.id), "plan_id": str(plan.id)},
        )
        return session.url

    @staticmethod
    def cancel_subscription(subscription: CustomerSubscription) -> CustomerSubscription:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True,
        )
        subscription.cancel_at_period_end = True
        subscription.save(update_fields=["cancel_at_period_end", "updated_at"])
        logger.info("subscription canceled at period end: %s", subscription.stripe_subscription_id)
        return subscription

    @staticmethod
    def get_active_subscription(customer) -> CustomerSubscription | None:
        return CustomerSubscription.objects.filter(
            customer=customer,
            status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING],
        ).first()

    @staticmethod
    def sync_from_stripe(stripe_sub_dict: dict) -> CustomerSubscription:
        stripe_sub_id = stripe_sub_dict.get("id")
        stripe_customer_id = stripe_sub_dict.get("customer")
        status = stripe_sub_dict.get("status", SubscriptionStatus.INCOMPLETE)

        plan = None
        items = stripe_sub_dict.get("items", {}).get("data", [])
        if items:
            price_id = items[0].get("price", {}).get("id")
            if price_id:
                plan = SubscriptionPlan.objects.filter(stripe_price_id=price_id).first()

        def _ts(val):
            if val is None:
                return None
            return datetime.fromtimestamp(val, tz=dt_timezone.utc)

        sub, _ = CustomerSubscription.objects.update_or_create(
            stripe_subscription_id=stripe_sub_id,
            defaults={
                "stripe_customer_id": stripe_customer_id,
                "status": status,
                "plan": plan,
                "current_period_start": _ts(stripe_sub_dict.get("current_period_start")),
                "current_period_end": _ts(stripe_sub_dict.get("current_period_end")),
                "cancel_at_period_end": stripe_sub_dict.get("cancel_at_period_end", False),
                "canceled_at": _ts(stripe_sub_dict.get("canceled_at")),
                "trial_end": _ts(stripe_sub_dict.get("trial_end")),
            },
        )
        return sub
