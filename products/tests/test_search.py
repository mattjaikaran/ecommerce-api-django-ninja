"""Tests for weighted full-text product search."""

import pytest
from django.test import Client

from api.config.constants import MIN_SEARCH_QUERY_LENGTH
from core.tests.factories import UserFactory
from products.services import ProductService
from products.tests.factories import ProductFactory, ProductTagFactory

pytestmark = pytest.mark.django_db


def _tagged(product, tag_name):
    """Create a tag with the given name and attach it to the product."""
    tag = ProductTagFactory(name=tag_name)
    tag.products.add(product)
    return tag


class TestProductServiceSearch:
    """Unit tests for ProductService.search_products."""

    def test_name_match_outranks_description_and_tag_matches(self):
        name_match = ProductFactory(
            name="Wireless Headphones", description="Audio gear"
        )
        desc_match = ProductFactory(
            name="Audio System",
            description="High quality wireless sound for home listening",
        )
        tag_match = ProductFactory(name="Audio Gadget", description="Portable sound")
        _tagged(tag_match, "wireless")

        results = list(ProductService.search_products("wireless"))

        assert [p.id for p in results] == [
            name_match.id,
            desc_match.id,
            tag_match.id,
        ]

    def test_phrase_match_outranks_scattered_keyword_match(self):
        phrase_match = ProductFactory(
            name="Wireless Headphones",
            description="Premium wireless headphones for music lovers",
        )
        scattered_match = ProductFactory(
            name="Audio Device",
            description=(
                "Wireless audio transmission with long battery life, "
                "durable build, and comfortable headphones for everyday use"
            ),
        )
        ProductFactory(name="Laptop Stand", description="Ergonomic desk accessory")

        results = list(ProductService.search_products("wireless headphones"))

        assert [p.id for p in results] == [phrase_match.id, scattered_match.id]

    def test_tag_only_match_is_found(self):
        product = ProductFactory(name="Audio Gadget", description="Portable sound")
        _tagged(product, "wireless")

        results = list(ProductService.search_products("wireless"))

        assert [p.id for p in results] == [product.id]

    def test_inactive_products_are_excluded(self):
        ProductFactory(name="Wireless Speaker", is_active=False)
        active = ProductFactory(name="Wireless Headphones", description="Audio gear")

        results = list(ProductService.search_products("wireless"))

        assert [p.id for p in results] == [active.id]

    def test_results_capped_at_max_search_results(self, monkeypatch):
        monkeypatch.setattr("products.services.product_service.MAX_SEARCH_RESULTS", 3)
        ProductFactory.create_batch(
            5, name="Wireless Headphones", description="Audio gear"
        )

        results = list(ProductService.search_products("wireless"))

        assert len(results) == 3


class TestSearchEndpoint:
    """Controller tests for the search parameter on the products list."""

    def setup_method(self):
        self.client = Client()
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_search_returns_ranked_results(self):
        name_match = ProductFactory(
            name="Wireless Headphones", description="Audio gear"
        )
        desc_match = ProductFactory(
            name="Audio System",
            description="High quality wireless sound for home listening",
        )
        tag_match = ProductFactory(name="Audio Gadget", description="Portable sound")
        _tagged(tag_match, "wireless")

        response = self.client.get("/api/products?search=wireless")

        assert response.status_code == 200
        data = response.json()
        assert [item["id"] for item in data] == [
            str(name_match.id),
            str(desc_match.id),
            str(tag_match.id),
        ]

    def test_empty_search_returns_normal_list(self):
        active = ProductFactory.create_batch(3)
        ProductFactory(is_active=False)

        response = self.client.get("/api/products?search=")

        assert response.status_code == 200
        data = response.json()
        assert {item["id"] for item in data} == {str(p.id) for p in active}

    def test_short_query_returns_normal_list(self):
        ProductFactory.create_batch(2)
        ProductFactory(is_active=False)

        query = "a" * (MIN_SEARCH_QUERY_LENGTH - 1)
        response = self.client.get(f"/api/products?search={query}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_explicit_ordering_overrides_rank(self):
        ProductFactory(name="Wireless Headphones", description="Audio gear")
        ProductFactory(
            name="Audio System",
            description="High quality wireless sound for home listening",
        )

        response = self.client.get("/api/products?search=wireless&ordering=name")

        assert response.status_code == 200
        data = response.json()
        names = [item["name"] for item in data]
        assert names == sorted(names)
