import pytest
from django.test import Client

from core.tests.factories import (
    AddressFactory,
    AdminUserFactory,
    CustomerFactory,
    UserFactory,
)
from orders.models import Order, OrderStatus
from orders.tests.factories import (
    ConfirmedOrderFactory,
    OrderFactory,
    OrderLineItemFactory,
)
from products.tests.factories import ProductVariantFactory


@pytest.mark.django_db
class TestOrderController:
    """Test operations for OrderController."""

    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        self.user = UserFactory()
        self.customer = CustomerFactory(user=self.user)
        self.admin_user = AdminUserFactory()
        self.client.force_login(self.user)

    def test_create_order(self):
        """Test creating a new order."""
        billing_address = AddressFactory(user=self.user, is_billing=True)
        shipping_address = AddressFactory(user=self.user, is_shipping=True)
        variant = ProductVariantFactory()

        order_data = {
            "customer_id": str(self.customer.id),
            "billing_address_id": str(billing_address.id),
            "shipping_address_id": str(shipping_address.id),
            "email": self.user.email,
            "subtotal": "100.00",
            "shipping_amount": "10.00",
            "tax_amount": "8.00",
            "total": "118.00",
            "items": [{"product_variant_id": str(variant.id), "quantity": 1, "unit_price": "100.00"}],
        }

        response = self.client.post(
            "/api/orders", data=order_data, content_type="application/json"
        )

        assert response.status_code == 201
        assert Order.objects.filter(customer=self.customer).exists()

        order = Order.objects.get(customer=self.customer)
        assert order.email == order_data["email"]
        # totals are computed by the service from items, not taken from submitted data
        assert order.total > 0

    def test_create_order_with_line_items(self):
        """Test creating an order with line items."""
        billing_address = AddressFactory(user=self.user, is_billing=True)
        shipping_address = AddressFactory(user=self.user, is_shipping=True)
        product_variant = ProductVariantFactory()

        order_data = {
            "customer_id": str(self.customer.id),
            "billing_address_id": str(billing_address.id),
            "shipping_address_id": str(shipping_address.id),
            "email": self.user.email,
            "subtotal": "100.00",
            "total": "108.00",
            "items": [
                {
                    "product_variant_id": str(product_variant.id),
                    "quantity": 2,
                    "unit_price": "50.00",
                }
            ],
        }

        response = self.client.post(
            "/api/orders", data=order_data, content_type="application/json"
        )

        assert response.status_code == 201
        order = Order.objects.get(customer=self.customer)
        assert order.items.count() == 1

        line_item = order.items.first()
        assert line_item.product_variant == product_variant
        assert line_item.quantity == 2

    def test_read_order_list(self):
        """Test retrieving list of orders."""
        OrderFactory.create_batch(3, customer=self.customer)

        response = self.client.get("/api/orders")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_read_order_list_filters(self):
        """Test filtering orders by various criteria."""
        draft_order = OrderFactory(customer=self.customer, status=OrderStatus.DRAFT)
        confirmed_order = ConfirmedOrderFactory(customer=self.customer)

        # Test status filter
        response = self.client.get(f"/api/orders?status={OrderStatus.PROCESSING}")
        assert response.status_code == 200
        data = response.json()
        order_ids = [item["id"] for item in data]
        assert str(confirmed_order.id) in order_ids
        assert str(draft_order.id) not in order_ids

    def test_read_order_detail(self):
        """Test retrieving a specific order."""
        order = OrderFactory(customer=self.customer)
        OrderLineItemFactory.create_batch(2, order=order)

        response = self.client.get(f"/api/orders/{order.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(order.id)
        assert data["order_number"] == order.order_number
        assert len(data["items"]) == 2

    def test_read_order_detail_not_found(self):
        """Test retrieving non-existent order returns 404."""
        import uuid

        fake_id = uuid.uuid4()

        response = self.client.get(f"/api/orders/{fake_id}")

        assert response.status_code == 404

    def test_update_order_status(self):
        """Test updating order status."""
        order = OrderFactory(customer=self.customer, status=OrderStatus.DRAFT)

        # Switch to admin for status updates
        self.client.force_login(self.admin_user)

        update_data = {"status": OrderStatus.PROCESSING}

        response = self.client.put(
            f"/api/orders/{order.id}",
            data=update_data,
            content_type="application/json",
        )

        assert response.status_code == 200
        order.refresh_from_db()
        assert order.status == OrderStatus.PROCESSING

    def test_update_order_customer_note(self):
        """Test updating order customer note."""
        order = OrderFactory(customer=self.customer)
        update_data = {"customer_note": "Please deliver to front door"}

        response = self.client.put(
            f"/api/orders/{order.id}",
            data=update_data,
            content_type="application/json",
        )

        assert response.status_code == 200
        order.refresh_from_db()
        assert order.customer_note == update_data["customer_note"]

    def test_cancel_order(self):
        """Test cancelling an order."""
        order = OrderFactory(customer=self.customer, status=OrderStatus.PENDING)

        response = self.client.post(f"/api/orders/{order.id}/cancel")

        assert response.status_code == 200
        order.refresh_from_db()
        assert order.status == OrderStatus.CANCELLED

    def test_delete_order(self):
        """Test deleting an order (soft delete)."""
        order = OrderFactory(customer=self.customer)

        # Switch to admin for deletion
        self.client.force_login(self.admin_user)

        response = self.client.delete(f"/api/orders/{order.id}")

        assert response.status_code == 204
        order.refresh_from_db()
        assert order.is_deleted is True

    def test_order_search(self):
        """Test searching orders by order number."""
        order1 = OrderFactory(customer=self.customer, order_number="ORD-001234")
        order2 = OrderFactory(customer=self.customer, order_number="ORD-005678")

        response = self.client.get("/api/orders?search=001234")

        assert response.status_code == 200
        data = response.json()
        order_numbers = [item["order_number"] for item in data]
        assert order1.order_number in order_numbers
        assert order2.order_number not in order_numbers

    def test_order_ordering(self):
        """Test ordering orders by date."""
        old_order = OrderFactory(customer=self.customer)
        new_order = OrderFactory(customer=self.customer)

        response = self.client.get("/api/orders?ordering=-created_at")

        assert response.status_code == 200
        data = response.json()
        order_ids = [item["id"] for item in data]
        new_index = order_ids.index(str(new_order.id))
        old_index = order_ids.index(str(old_order.id))
        assert new_index < old_index


@pytest.mark.django_db
class TestOrderControllerPermissions:
    """Test permission requirements for OrderController."""

    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        self.user = UserFactory()
        self.customer = CustomerFactory(user=self.user)
        self.other_user = UserFactory()
        self.other_customer = CustomerFactory(user=self.other_user)
        self.admin_user = AdminUserFactory()

    def test_order_list_requires_authentication(self):
        """Test that order list endpoint requires authentication."""
        response = self.client.get("/api/orders")

        assert response.status_code == 401

    def test_user_can_only_see_own_orders(self):
        """Test that users can only see their own orders."""
        own_order = OrderFactory(customer=self.customer)
        other_order = OrderFactory(customer=self.other_customer)

        self.client.force_login(self.user)
        response = self.client.get("/api/orders")

        assert response.status_code == 200
        data = response.json()
        order_ids = [item["id"] for item in data]

        assert str(own_order.id) in order_ids
        assert str(other_order.id) not in order_ids

    def test_user_cannot_access_other_users_order(self):
        """Test that users cannot access other users' orders."""
        other_order = OrderFactory(customer=self.other_customer)

        self.client.force_login(self.user)
        response = self.client.get(f"/api/orders/{other_order.id}")

        assert response.status_code == 404

    def test_admin_can_access_all_orders(self):
        """Test that admin can access all orders."""
        user_order = OrderFactory(customer=self.customer)

        self.client.force_login(self.admin_user)
        response = self.client.get(f"/api/orders/{user_order.id}")

        assert response.status_code == 200

    def test_only_admin_can_update_order_status(self):
        """Test that only admin can update order status."""
        order = OrderFactory(customer=self.customer, status=OrderStatus.DRAFT)
        update_data = {"status": OrderStatus.PROCESSING}

        # Test regular user cannot update status
        self.client.force_login(self.user)
        response = self.client.put(
            f"/api/orders/{order.id}",
            data=update_data,
            content_type="application/json",
        )
        # This might return 200 but status should not change, or 403
        order.refresh_from_db()
        assert order.status == OrderStatus.DRAFT  # Should remain unchanged

    def test_user_can_cancel_own_order(self):
        """Test that user can cancel their own order."""
        order = OrderFactory(customer=self.customer, status=OrderStatus.PENDING)

        self.client.force_login(self.user)
        response = self.client.post(f"/api/orders/{order.id}/cancel")

        assert response.status_code == 200
        order.refresh_from_db()
        assert order.status == OrderStatus.CANCELLED

    def test_user_cannot_cancel_shipped_order(self):
        """Test that user cannot cancel already shipped order."""
        order = OrderFactory(customer=self.customer, status=OrderStatus.SHIPPED)

        self.client.force_login(self.user)
        response = self.client.post(f"/api/orders/{order.id}/cancel")

        assert response.status_code == 400
