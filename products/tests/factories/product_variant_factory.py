from decimal import Decimal

import factory

from core.tests.factories import UserFactory
from products.models import ProductVariant

from .product_factory import ProductFactory


class ProductVariantFactory(factory.django.DjangoModelFactory):
    """Factory for creating ProductVariant instances."""

    class Meta:
        model = ProductVariant

    product = factory.SubFactory(ProductFactory)
    name = factory.Faker("word")
    sku = factory.Sequence(lambda n: f"SKU-{n:06d}")
    barcode = factory.Faker("ean13")
    price = factory.Faker(
        "pydecimal",
        left_digits=3,
        right_digits=2,
        positive=True,
        min_value=Decimal("1.00"),
        max_value=Decimal("999.99"),
    )
    compare_at_price = factory.LazyAttribute(lambda obj: obj.price + Decimal("10.00"))
    cost_price = factory.LazyAttribute(lambda obj: obj.price - Decimal("5.00"))
    inventory_quantity = factory.Faker("random_int", min=0, max=100)
    low_stock_threshold = 10
    weight = factory.Faker(
        "pydecimal",
        left_digits=1,
        right_digits=2,
        positive=True,
        min_value=Decimal("0.10"),
        max_value=Decimal("9.99"),
    )
    length = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
        min_value=Decimal("1.00"),
        max_value=Decimal("99.99"),
    )
    width = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
        min_value=Decimal("1.00"),
        max_value=Decimal("99.99"),
    )
    height = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
        min_value=Decimal("1.00"),
        max_value=Decimal("99.99"),
    )
    position = factory.Sequence(lambda n: n)
    is_active = True
    meta_data = factory.LazyFunction(dict)
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute("created_by")


class InStockVariantFactory(ProductVariantFactory):
    """Factory for creating in-stock ProductVariant instances."""

    inventory_quantity = factory.Faker("random_int", min=20, max=100)


class OutOfStockVariantFactory(ProductVariantFactory):
    """Factory for creating out-of-stock ProductVariant instances."""

    inventory_quantity = 0


class LowStockVariantFactory(ProductVariantFactory):
    """Factory for creating low-stock ProductVariant instances."""

    inventory_quantity = factory.Faker("random_int", min=1, max=9)
    low_stock_threshold = 10
