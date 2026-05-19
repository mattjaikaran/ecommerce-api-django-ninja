from unittest.mock import MagicMock, patch

import pytest

from subscriptions.models import CustomerSubscription, SubscriptionPlan
from subscriptions.models.customer_subscription import SubscriptionStatus
from subscriptions.services import SubscriptionService
from subscriptions.tests.factories import CustomerSubscriptionFactory, SubscriptionPlanFactory


@pytest.mark.django_db
class TestSubscriptionPlan:
    def test_create_plan(self):
        plan = SubscriptionPlanFactory()
        assert plan.id is not None
        assert plan.is_active is True

    def test_plan_list_filters_inactive(self):
        SubscriptionPlanFactory(is_active=True)
        SubscriptionPlanFactory(is_active=False)
        active = SubscriptionPlan.objects.filter(is_active=True)
        assert active.count() == 1


@pytest.mark.django_db
class TestSubscriptionSync:
    def test_sync_from_stripe_creates_subscription(self):
        plan = SubscriptionPlanFactory(stripe_price_id="price_abc123")

        stripe_data = {
            "id": "sub_newone",
            "customer": "cus_abc",
            "status": "active",
            "current_period_start": 1700000000,
            "current_period_end": 1702000000,
            "cancel_at_period_end": False,
            "canceled_at": None,
            "trial_end": None,
            "items": {
                "data": [
                    {"price": {"id": "price_abc123"}}
                ]
            },
        }

        sub = SubscriptionService.sync_from_stripe(stripe_data)
        assert sub.stripe_subscription_id == "sub_newone"
        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.plan == plan

    def test_sync_from_stripe_updates_existing(self):
        existing = CustomerSubscriptionFactory(
            stripe_subscription_id="sub_existing",
            status=SubscriptionStatus.INCOMPLETE,
        )

        stripe_data = {
            "id": "sub_existing",
            "customer": "cus_xyz",
            "status": "active",
            "current_period_start": None,
            "current_period_end": None,
            "cancel_at_period_end": False,
            "canceled_at": None,
            "trial_end": None,
            "items": {"data": []},
        }

        sub = SubscriptionService.sync_from_stripe(stripe_data)
        assert sub.id == existing.id
        assert sub.status == SubscriptionStatus.ACTIVE

    def test_sync_canceled_subscription(self):
        stripe_data = {
            "id": "sub_canceled",
            "customer": "cus_abc",
            "status": "canceled",
            "current_period_start": None,
            "current_period_end": None,
            "cancel_at_period_end": True,
            "canceled_at": 1700500000,
            "trial_end": None,
            "items": {"data": []},
        }

        sub = SubscriptionService.sync_from_stripe(stripe_data)
        assert sub.status == SubscriptionStatus.CANCELED
        assert sub.cancel_at_period_end is True
        assert sub.canceled_at is not None


@pytest.mark.django_db
class TestSubscriptionCancellation:
    def test_cancel_subscription(self):
        sub = CustomerSubscriptionFactory(
            status=SubscriptionStatus.ACTIVE,
            cancel_at_period_end=False,
        )

        with patch("subscriptions.services.subscription_service.stripe") as mock_stripe:
            mock_stripe.Subscription.modify.return_value = {}
            result = SubscriptionService.cancel_subscription(sub)

        result.refresh_from_db()
        assert result.cancel_at_period_end is True
