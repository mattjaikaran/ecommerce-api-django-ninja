"""Factory for ProductCategory model."""

import factory

from core.tests.factories import UserFactory
from products.models import ProductCategory


class ProductCategoryFactory(factory.django.DjangoModelFactory):
    """Factory for creating ProductCategory instances."""

    class Meta:
        model = ProductCategory

    name = factory.Faker("word")
    slug = factory.Sequence(lambda n: f"category-{n}")
    description = factory.Faker("text", max_nb_chars=200)
    parent = None
    seo_title = factory.LazyAttribute(lambda obj: f"{obj.name} - Category")
    seo_description = factory.Faker("text", max_nb_chars=160)
    seo_keywords = factory.Faker("words", nb=5)
    is_active = True
    position = factory.Sequence(lambda n: n)
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute("created_by")


class SubCategoryFactory(ProductCategoryFactory):
    """Factory for creating subcategory ProductCategory instances."""

    parent = factory.SubFactory(ProductCategoryFactory)
