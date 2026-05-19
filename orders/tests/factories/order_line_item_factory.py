from decimal import Decimal

import factory

from orders.models import OrderLineItem
from products.tests.factories import ProductVariantFactory

from .order_factory import OrderFactory


class OrderLineItemFactory(factory.django.DjangoModelFactory):
    """Factory for creating OrderLineItem instances."""

    class Meta:
        model = OrderLineItem

    order = factory.SubFactory(OrderFactory)
    product_variant = factory.SubFactory(ProductVariantFactory)
    quantity = factory.Faker("random_int", min=1, max=5)
    unit_price = factory.LazyAttribute(lambda obj: obj.product_variant.price)
    subtotal = factory.LazyAttribute(lambda obj: obj.unit_price * obj.quantity)
    discount_amount = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
        min_value=Decimal("0.01"),
        max_value=Decimal("10.00"),
    )
    tax_amount = factory.LazyAttribute(
        lambda obj: obj.subtotal * Decimal("0.08")
    )  # 8% tax
    total = factory.LazyAttribute(
        lambda obj: obj.subtotal + obj.tax_amount - obj.discount_amount
    )
    tax_rate = Decimal("0.08")
    weight = factory.LazyAttribute(
        lambda obj: obj.product_variant.weight or Decimal("0.00")
    )
    meta_data = factory.LazyFunction(dict)
    created_by = factory.SelfAttribute("order.customer.user")
    updated_by = factory.SelfAttribute("order.customer.user")


class SingleItemLineFactory(OrderLineItemFactory):
    """Factory for creating single quantity OrderLineItem instances."""

    quantity = 1


class BulkItemLineFactory(OrderLineItemFactory):
    """Factory for creating bulk quantity OrderLineItem instances."""

    quantity = factory.Faker("random_int", min=5, max=20)
