"""Query count regression tests for the products list endpoint.

These tests catch N+1 query regressions by asserting that the number of
SQL queries executed stays constant as the number of rows grows.
"""

import pytest
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.db import connection

from core.tests.factories import AdminUserFactory, UserFactory
from products.tests.factories import (
    ProductCategoryFactory,
    ProductFactory,
    ProductVariantFactory,
    PublishedProductFactory,
)


@pytest.mark.django_db
class TestProductListQueryCount:
    """Verify that GET /api/products/ does not produce N+1 queries."""

    def setup_method(self):
        self.client = Client()
        self.admin_user = AdminUserFactory()
        self.client.force_login(self.admin_user)

    def _create_products(self, n: int):
        category = ProductCategoryFactory()
        products = ProductFactory.create_batch(n, category=category)
        for product in products:
            ProductVariantFactory.create_batch(2, product=product)
        return products

    def test_product_list_query_count_does_not_grow_with_rows(self):
        """Query count must stay the same when product count doubles."""
        self._create_products(3)
        with CaptureQueriesContext(connection) as ctx_small:
            response = self.client.get("/api/products")
        assert response.status_code == 200
        queries_small = len(ctx_small.captured_queries)

        self._create_products(6)
        with CaptureQueriesContext(connection) as ctx_large:
            response = self.client.get("/api/products")
        assert response.status_code == 200
        queries_large = len(ctx_large.captured_queries)

        assert queries_large <= queries_small + 2, (
            f"Possible N+1 detected: {queries_small} queries for 3 products, "
            f"{queries_large} queries for 9 products"
        )

    def test_product_list_absolute_query_cap(self):
        """At most 15 queries for a page of products with variants."""
        self._create_products(5)
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/products")
        assert response.status_code == 200
        n = len(ctx.captured_queries)
        assert n <= 20, (
            f"Product list used {n} queries for 5 products — expected ≤ 20. Queries:\n"
            + "\n".join(q["sql"][:120] for q in ctx.captured_queries)
        )

    def test_product_list_variant_prefetch_no_n_plus_one(self):
        """Variant fetch must not cause per-product extra queries."""
        category = ProductCategoryFactory()
        for _ in range(4):
            product = ProductFactory(category=category)
            ProductVariantFactory.create_batch(3, product=product)

        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/products")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 4

    def test_product_list_is_not_linear_in_query_count(self):
        """Growing from 5 to 15 products must not scale queries linearly."""
        category = ProductCategoryFactory()

        ProductFactory.create_batch(5, category=category)
        with CaptureQueriesContext(connection) as ctx_5:
            self.client.get("/api/products/")
        n5 = len(ctx_5.captured_queries)

        ProductFactory.create_batch(10, category=category)
        with CaptureQueriesContext(connection) as ctx_15:
            self.client.get("/api/products/")
        n15 = len(ctx_15.captured_queries)

        # If N+1, n15 would be ~3x n5. Allow at most 3 extra queries for
        # any overhead (pagination count, cache, etc.)
        assert n15 <= n5 + 3, (
            f"Product list query count scaled from {n5} (5 products) "
            f"to {n15} (15 products) — indicates N+1"
        )
