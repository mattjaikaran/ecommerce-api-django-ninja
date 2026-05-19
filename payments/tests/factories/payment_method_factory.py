"""Factories for PaymentMethod model."""

import factory

from core.tests.factories import UserFactory
from payments.models import PaymentMethod


class PaymentMethodFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PaymentMethod

    type = "card"
    provider = "stripe"
    is_default = False
    stripe_payment_method_id = factory.Sequence(lambda n: f"pm_test_{n:06d}")
    stripe_customer_id = factory.Sequence(lambda n: f"cus_test_{n:06d}")
    last_four = factory.Faker("numerify", text="####")
    card_brand = factory.Iterator(["visa", "mastercard", "amex"])
    expiry_month = factory.Faker("random_int", min=1, max=12)
    expiry_year = factory.Faker("random_int", min=2025, max=2030)
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute("created_by")
