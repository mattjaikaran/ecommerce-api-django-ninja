import factory

from core.tests.factories import UserFactory
from products.models import ProductTag


class ProductTagFactory(factory.django.DjangoModelFactory):
    """Factory for creating ProductTag instances."""

    class Meta:
        model = ProductTag

    name = factory.Faker("word")
    slug = factory.Sequence(lambda n: f"tag-{n}")
    description = factory.Faker("sentence")
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute("created_by")

    @factory.post_generation
    def products(self, create, extracted, **kwargs):
        """Attach products to the tag when passed as ``products=[...]``."""
        if create and extracted:
            self.products.add(*extracted)
