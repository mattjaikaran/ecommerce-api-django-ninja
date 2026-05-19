from decimal import Decimal

import factory

from core.tests.factories import UserFactory
from products.models import Product
from products.models.choices import ProductStatus, ProductType, ShippingClass, TaxClass

from .product_category_factory import ProductCategoryFactory


class ProductFactory(factory.django.DjangoModelFactory):
    """Factory for creating Product instances."""

    class Meta:
        model = Product

    name = factory.Faker("word")
    slug = factory.Sequence(lambda n: f"product-{n}")
    description = factory.Faker("text", max_nb_chars=500)
    category = factory.SubFactory(ProductCategoryFactory)
    type = ProductType.PHYSICAL
    tax_class = TaxClass.STANDARD
    shipping_class = ShippingClass.STANDARD
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
    quantity = factory.Faker("random_int", min=0, max=100)
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
    download_limit = None
    is_active = True
    status = ProductStatus.ACTIVE
    featured = False
    seo_title = factory.LazyAttribute(lambda obj: f"{obj.name} - Product")
    seo_description = factory.Faker("text", max_nb_chars=160)
    seo_keywords = factory.Faker("words", nb=5)
    meta_data = factory.LazyFunction(dict)
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute("created_by")


class PublishedProductFactory(ProductFactory):
    """Factory for creating published Product instances."""

    status = ProductStatus.ACTIVE
    is_active = True


class FeaturedProductFactory(PublishedProductFactory):
    """Factory for creating featured Product instances."""

    featured = True


class DigitalProductFactory(ProductFactory):
    """Factory for creating digital Product instances."""

    type = ProductType.DIGITAL
    download_limit = factory.Faker("random_int", min=1, max=10)
    weight = None
    length = None
    width = None
    height = None
