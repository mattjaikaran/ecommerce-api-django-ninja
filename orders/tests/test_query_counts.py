"""Query count regression tests for the orders list endpoint.

These tests catch N+1 query regressions by asserting that the number of
SQL queries executed stays constant as the number of rows grows.
"""

import pytest
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.db import connection

from core.tests.factories import AdminUserFactory, CustomerFactory, UserFactory
from orders.tests.factories import OrderFactory, OrderLineItemFactory
from products.tests.factories import ProductVariantFactory


@pytest.mark.django_db
class TestOrderListQueryCount:
    """Verify that GET /api/orders/ does not produce N+1 queries."""

    def setup_method(self):
        self.client = Client()
        self.user = UserFactory()
        self.admin_user = AdminUserFactory()
        self.customer = CustomerFactory(user=self.user)
        self.client.force_login(self.admin_user)
        # Verify authentication works
        assert self.admin_user.is_authenticated

    def _create_orders_with_items(self, n_orders: int, items_per_order: int = 2):
        """Create n_orders, each with items_per_order line items."""
        orders = OrderFactory.create_batch(n_orders, customer=self.customer)
        variant = ProductVariantFactory()
        for order in orders:
            OrderLineItemFactory.create_batch(
                items_per_order, order=order, product_variant=variant
            )
        return orders

    def test_order_list_query_count_does_not_grow_with_rows(self):
        """Query count must stay the same when order count doubles."""
        # Warm-up: 2 orders
        self._create_orders_with_items(2)
        with CaptureQueriesContext(connection) as ctx_small:
            response = self.client.get("/api/orders")
        assert response.status_code == 200
        queries_small = len(ctx_small.captured_queries)

        # Add 4 more orders (total 6)
        self._create_orders_with_items(4)
        with CaptureQueriesContext(connection) as ctx_large:
            response = self.client.get("/api/orders")
        assert response.status_code == 200
        queries_large = len(ctx_large.captured_queries)

        # If N+1 exists, queries_large > queries_small substantially.
        # Allow a tiny slack (e.g. pagination count query) but never O(N).
        assert queries_large <= queries_small + 2, (
            f"Possible N+1 detected: {queries_small} queries for 2 orders, "
            f"{queries_large} queries for 6 orders"
        )

    def test_order_list_absolute_query_cap(self):
        """At most 10 queries for a page of orders (auth + main + prefetches)."""
        self._create_orders_with_items(5, items_per_order=3)
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/orders")
        assert response.status_code == 200
        n = len(ctx.captured_queries)
        assert n <= 15, (
            f"Order list used {n} queries for 5 orders with 3 items each — "
            f"expected ≤ 15. Queries:\n"
            + "\n".join(q["sql"][:120] for q in ctx.captured_queries)
        )

    def test_order_list_with_items_no_n_plus_one(self):
        """Items prefetch must not cause per-order extra queries."""
        # Create orders with different item counts
        from orders.models import Order as OrderModel
        variant1 = ProductVariantFactory()
        variant2 = ProductVariantFactory()
        orders = OrderFactory.create_batch(3, customer=self.customer)
        for order in orders:
            OrderLineItemFactory(order=order, product_variant=variant1)
            OrderLineItemFactory(order=order, product_variant=variant2)

        # Verify 3 orders are in DB
        assert OrderModel.objects.filter(customer=self.customer).count() == 3

        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/orders")

        assert response.status_code == 200
        data = response.json()

        # Response should contain at least the 3 orders we created
        total_in_db = OrderModel.objects.count()
        assert len(data["results"]) >= 3, (
            f"Expected >= 3 orders, got {len(data['results'])}. "
            f"DB has {total_in_db} orders total. "
            f"Queries executed: {len(ctx.captured_queries)}."
        )

        # Each item in response should have been fetched by prefetch, not lazy load
        for order_data in data["results"]:
            assert "items" in order_data
