import factory

from subscriptions.models import CustomerSubscription, SubscriptionPlan
from subscriptions.models.customer_subscription import SubscriptionStatus
from subscriptions.models.subscription_plan import BillingInterval


class SubscriptionPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SubscriptionPlan

    name = factory.Sequence(lambda n: f"Plan {n}")
    stripe_price_id = factory.Sequence(lambda n: f"price_test_{n}")
    stripe_product_id = factory.Sequence(lambda n: f"prod_test_{n}")
    interval = BillingInterval.MONTHLY
    amount = factory.Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    currency = "usd"
    features = []
    is_active = True


class CustomerSubscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomerSubscription

    stripe_subscription_id = factory.Sequence(lambda n: f"sub_test_{n}")
    stripe_customer_id = factory.Sequence(lambda n: f"cus_test_{n}")
    status = SubscriptionStatus.ACTIVE
    cancel_at_period_end = False
