from datetime import timedelta
from decimal import Decimal

import factory
from django.utils import timezone

from cart.models import Cart
from core.tests.factories import CustomerFactory, UserFactory


class CartFactory(factory.django.DjangoModelFactory):
    """Factory for creating Cart instances."""

    class Meta:
        model = Cart

    session_key = factory.Faker("uuid4")
    expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(days=30))
    customer = factory.SubFactory(CustomerFactory)
    subtotal = factory.Faker(
        "pydecimal",
        left_digits=3,
        right_digits=2,
        positive=True,
        min_value=Decimal("0.01"),
        max_value=Decimal("999.99"),
    )
    total_price = factory.LazyAttribute(lambda obj: obj.subtotal)
    total_quantity = factory.Faker("random_int", min=1, max=10)
    is_active = True
    created_by = factory.SelfAttribute("customer.user")
    updated_by = factory.SelfAttribute("customer.user")


class AnonymousCartFactory(CartFactory):
    """Factory for creating anonymous Cart instances."""

    customer = None
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute("created_by")


class ExpiredCartFactory(CartFactory):
    """Factory for creating expired Cart instances."""

    expires_at = factory.LazyFunction(lambda: timezone.now() - timedelta(days=1))


class EmptyCartFactory(CartFactory):
    """Factory for creating empty Cart instances."""

    subtotal = Decimal("0.00")
    total_price = Decimal("0.00")
    total_quantity = 0
