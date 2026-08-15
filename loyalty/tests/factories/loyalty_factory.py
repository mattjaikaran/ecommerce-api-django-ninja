from decimal import Decimal

import factory

from core.tests.factories import CustomerFactory
from loyalty.models import LoyaltyAccount, LoyaltyReason, LoyaltyTransaction


class LoyaltyAccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LoyaltyAccount

    customer = factory.SubFactory(CustomerFactory)
    balance = Decimal("0.00")
    lifetime_points = Decimal("0.00")
    created_by = factory.SelfAttribute("customer.user")
    updated_by = factory.SelfAttribute("customer.user")


class LoyaltyTransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LoyaltyTransaction

    account = factory.SubFactory(LoyaltyAccountFactory)
    amount = Decimal("100.00")
    order = None
    reason = LoyaltyReason.EARN
    reference = ""
    created_by = factory.SelfAttribute("account.customer.user")
    updated_by = factory.SelfAttribute("account.customer.user")
