"""Tests for OrderService business logic.

Covers all service methods:
- create_order
- assert_editable
- update_order
- add_item
- update_item
- remove_item
- submit_order
- cancel_order
- delete_order
"""

from decimal import Decimal

import pytest

from api.exceptions import ValidationError
from core.tests.factories import (
    AddressFactory,
    CustomerFactory,
    CustomerGroupFactory,
    UserFactory,
)
from orders.models import Order, OrderLineItem, OrderStatus
from orders.schemas import (
    OrderCreateSchema,
    OrderLineItemCreateSchema,
    OrderLineItemUpdateSchema,
    OrderUpdateSchema,
)
from orders.services import OrderService
from orders.tests.factories import (
    CancelledOrderFactory,
    ConfirmedOrderFactory,
    DeliveredOrderFactory,
    DraftOrderFactory,
    OrderFactory,
    OrderLineItemFactory,
    ShippedOrderFactory,
)
from products.tests.factories import ProductVariantFactory

pytestmark = pytest.mark.django_db


class TestOrderServiceCreateOrder:
    def _make_payload(self, customer, user, billing_address=None, shipping_address=None, items=None):
        if billing_address is None:
            billing_address = AddressFactory(user=user, is_billing=True)
        if shipping_address is None:
            shipping_address = AddressFactory(user=user, is_shipping=True)
        if items is None:
            items = []
        return OrderCreateSchema(
            customer_id=customer.id,
            billing_address_id=billing_address.id,
            shipping_address_id=shipping_address.id,
            email=user.email,
            items=items,
        )

    def test_create_order_basic(self):
        user = UserFactory()
        customer = CustomerFactory(user=user)
        payload = self._make_payload(customer, user)

        order = OrderService.create_order(payload, user, {})

        assert order.pk is not None
        assert order.customer == customer
        assert order.email == user.email
        assert order.status == OrderStatus.DRAFT
        assert order.subtotal == Decimal("0.00")
        assert order.total == Decimal("0.00")

    def test_create_order_with_items_calculates_subtotal(self):
        user = UserFactory()
        customer = CustomerFactory(user=user)
        variant = ProductVariantFactory(price=Decimal("25.00"))

        payload = self._make_payload(customer, user, items=[
            {"product_variant_id": str(variant.id), "quantity": 2},
        ])

        order = OrderService.create_order(payload, user, {})

        assert order.items.count() == 1
        line = order.items.first()
        assert line.quantity == 2
        # subtotal = order item total (unit_price * quantity + tax - discount)
        assert order.subtotal == line.total
        assert order.total == line.total

    def test_create_order_multiple_items(self):
        user = UserFactory()
        customer = CustomerFactory(user=user)
        variant1 = ProductVariantFactory(price=Decimal("10.00"))
        variant2 = ProductVariantFactory(price=Decimal("20.00"))

        payload = self._make_payload(customer, user, items=[
            {"product_variant_id": str(variant1.id), "quantity": 1},
            {"product_variant_id": str(variant2.id), "quantity": 3},
        ])

        order = OrderService.create_order(payload, user, {})

        assert order.items.count() == 2
        expected_subtotal = sum(item.total for item in order.items.all())
        assert order.subtotal == expected_subtotal

    def test_create_order_stores_ip_and_user_agent(self):
        user = UserFactory()
        customer = CustomerFactory(user=user)
        payload = self._make_payload(customer, user)
        meta = {"REMOTE_ADDR": "192.168.1.100", "HTTP_USER_AGENT": "TestAgent/1.0"}

        order = OrderService.create_order(payload, user, meta)

        assert order.ip_address == "192.168.1.100"
        assert order.user_agent == "TestAgent/1.0"

    def test_create_order_sets_created_by(self):
        user = UserFactory()
        customer = CustomerFactory(user=user)
        payload = self._make_payload(customer, user)

        order = OrderService.create_order(payload, user, {})

        assert order.created_by == user
        assert order.updated_by == user

    def test_create_order_with_customer_group(self):
        user = UserFactory()
        customer = CustomerFactory(user=user)
        group = CustomerGroupFactory()
        billing = AddressFactory(user=user, is_billing=True)
        shipping = AddressFactory(user=user, is_shipping=True)
        payload = OrderCreateSchema(
            customer_id=customer.id,
            customer_group_id=group.id,
            billing_address_id=billing.id,
            shipping_address_id=shipping.id,
            email=user.email,
            items=[],
        )

        order = OrderService.create_order(payload, user, {})

        assert order.customer_group == group


class TestOrderServiceAssertEditable:
    def test_draft_order_is_editable(self):
        order = DraftOrderFactory()
        # Should not raise
        OrderService.assert_editable(order)

    def test_pending_order_is_editable(self):
        order = OrderFactory(status=OrderStatus.PENDING)
        OrderService.assert_editable(order)

    def test_processing_order_is_not_editable(self):
        order = ConfirmedOrderFactory()
        with pytest.raises(ValidationError, match="cannot be updated"):
            OrderService.assert_editable(order)

    def test_shipped_order_is_not_editable(self):
        order = ShippedOrderFactory()
        with pytest.raises(ValidationError, match="cannot be updated"):
            OrderService.assert_editable(order)

    def test_cancelled_order_is_not_editable(self):
        order = CancelledOrderFactory()
        with pytest.raises(ValidationError, match="cannot be updated"):
            OrderService.assert_editable(order)

    def test_delivered_order_is_not_editable(self):
        order = DeliveredOrderFactory()
        with pytest.raises(ValidationError, match="cannot be updated"):
            OrderService.assert_editable(order)


class TestOrderServiceUpdateOrder:
    def test_update_order_customer_note(self):
        user = UserFactory()
        order = DraftOrderFactory()
        payload = OrderUpdateSchema(customer_note="Please ring the bell")

        updated = OrderService.update_order(order, payload, user)

        assert updated.customer_note == "Please ring the bell"
        assert updated.updated_by == user

    def test_update_order_email(self):
        user = UserFactory()
        order = DraftOrderFactory()
        payload = OrderUpdateSchema(email="new@example.com")

        updated = OrderService.update_order(order, payload, user)

        order.refresh_from_db()
        assert order.email == "new@example.com"

    def test_update_order_only_sets_provided_fields(self):
        user = UserFactory()
        original_email = "original@example.com"
        order = DraftOrderFactory(email=original_email)
        payload = OrderUpdateSchema(customer_note="note only")

        OrderService.update_order(order, payload, user)

        order.refresh_from_db()
        assert order.email == original_email
        assert order.customer_note == "note only"

    def test_update_non_editable_order_raises(self):
        user = UserFactory()
        order = ShippedOrderFactory()
        payload = OrderUpdateSchema(customer_note="too late")

        with pytest.raises(ValidationError):
            OrderService.update_order(order, payload, user)


class TestOrderServiceAddItem:
    def test_add_item_to_draft_order(self):
        user = UserFactory()
        order = DraftOrderFactory(subtotal=Decimal("0.00"), total=Decimal("0.00"))
        variant = ProductVariantFactory(price=Decimal("15.00"))
        payload = OrderLineItemCreateSchema(product_variant_id=variant.id, quantity=2)

        item = OrderService.add_item(order, payload, user)

        assert item.order == order
        assert item.product_variant == variant
        assert item.quantity == 2
        order.refresh_from_db()
        assert order.subtotal == item.total
        assert order.total == item.total

    def test_add_item_updates_order_totals(self):
        user = UserFactory()
        existing_item = OrderLineItemFactory()
        order = existing_item.order
        order.subtotal = existing_item.total
        order.total = existing_item.total
        order.save()
        # Refresh to get DB-rounded values (DecimalField max 2dp)
        order.refresh_from_db()
        subtotal_before = order.subtotal

        variant = ProductVariantFactory(price=Decimal("10.00"))
        payload = OrderLineItemCreateSchema(product_variant_id=variant.id, quantity=1)
        new_item = OrderService.add_item(order, payload, user)

        order.refresh_from_db()
        # The order.subtotal was subtotal_before + new_item.total
        assert order.subtotal == subtotal_before + new_item.total
        assert order.total == order.subtotal

    def test_add_item_to_non_editable_order_raises(self):
        user = UserFactory()
        order = ShippedOrderFactory()
        variant = ProductVariantFactory()
        payload = OrderLineItemCreateSchema(product_variant_id=variant.id, quantity=1)

        with pytest.raises(ValidationError):
            OrderService.add_item(order, payload, user)

    def test_add_item_sets_created_by(self):
        user = UserFactory()
        order = DraftOrderFactory()
        variant = ProductVariantFactory()
        payload = OrderLineItemCreateSchema(product_variant_id=variant.id, quantity=1)

        item = OrderService.add_item(order, payload, user)

        assert item.created_by == user
        assert item.updated_by == user


class TestOrderServiceUpdateItem:
    def test_update_item_quantity(self):
        user = UserFactory()
        # Use a clean price to avoid precision issues
        variant = ProductVariantFactory(price=Decimal("10.00"))
        item = OrderLineItemFactory(
            quantity=1,
            product_variant=variant,
            unit_price=Decimal("10.00"),
            subtotal=Decimal("10.00"),
            total=Decimal("10.00"),
        )
        order = item.order
        order.subtotal = Decimal("10.00")
        order.total = Decimal("10.00")
        order.status = OrderStatus.DRAFT
        order.save()

        payload = OrderLineItemUpdateSchema(quantity=5)
        updated_item = OrderService.update_item(order, item, payload, user)

        assert updated_item.quantity == 5
        assert updated_item.total == Decimal("50.00")
        order.refresh_from_db()
        assert order.subtotal == Decimal("50.00")
        assert order.total == Decimal("50.00")

    def test_update_item_recalculates_order_subtotal(self):
        user = UserFactory()
        variant = ProductVariantFactory(price=Decimal("5.00"))
        item = OrderLineItemFactory(
            quantity=2,
            product_variant=variant,
            unit_price=Decimal("5.00"),
            subtotal=Decimal("10.00"),
            total=Decimal("10.00"),
        )
        order = item.order
        order.subtotal = Decimal("10.00")
        order.total = Decimal("10.00")
        order.status = OrderStatus.DRAFT
        order.save()

        payload = OrderLineItemUpdateSchema(quantity=4)
        OrderService.update_item(order, item, payload, user)

        order.refresh_from_db()
        item.refresh_from_db()
        # quantity doubled → total doubled
        assert order.subtotal == Decimal("20.00")
        assert item.total == Decimal("20.00")

    def test_update_item_on_non_editable_order_raises(self):
        user = UserFactory()
        item = OrderLineItemFactory()
        order = item.order
        order.status = OrderStatus.SHIPPED
        order.save()
        payload = OrderLineItemUpdateSchema(quantity=1)

        with pytest.raises(ValidationError):
            OrderService.update_item(order, item, payload, user)


class TestOrderServiceRemoveItem:
    def test_remove_item_deletes_line_item(self):
        user = UserFactory()
        item = OrderLineItemFactory()
        order = item.order
        order.subtotal = item.total
        order.total = item.total
        order.status = OrderStatus.DRAFT
        order.save()
        item_id = item.id

        OrderService.remove_item(order, item, user)

        assert not OrderLineItem.objects.filter(id=item_id).exists()

    def test_remove_item_updates_order_totals(self):
        user = UserFactory()
        item = OrderLineItemFactory()
        order = item.order
        initial_subtotal = item.total
        order.subtotal = initial_subtotal
        order.total = initial_subtotal
        order.status = OrderStatus.DRAFT
        order.save()

        OrderService.remove_item(order, item, user)

        order.refresh_from_db()
        assert order.subtotal == initial_subtotal - item.total

    def test_remove_item_from_non_editable_order_raises(self):
        user = UserFactory()
        item = OrderLineItemFactory()
        order = item.order
        order.status = OrderStatus.SHIPPED
        order.save()

        with pytest.raises(ValidationError):
            OrderService.remove_item(order, item, user)


class TestOrderServiceSubmitOrder:
    def test_submit_draft_order_with_items(self):
        user = UserFactory()
        order = DraftOrderFactory()
        OrderLineItemFactory(order=order)

        submitted = OrderService.submit_order(order, user)

        assert submitted.status == OrderStatus.PENDING
        assert submitted.updated_by == user

    def test_submit_order_without_items_raises(self):
        user = UserFactory()
        order = DraftOrderFactory()
        # Ensure no items
        order.items.all().delete()

        with pytest.raises(ValidationError, match="at least one item"):
            OrderService.submit_order(order, user)

    def test_submit_non_draft_order_raises(self):
        user = UserFactory()
        order = ConfirmedOrderFactory()
        OrderLineItemFactory(order=order)

        with pytest.raises(ValidationError, match="Only draft orders"):
            OrderService.submit_order(order, user)

    def test_submit_cancelled_order_raises(self):
        user = UserFactory()
        order = CancelledOrderFactory()
        OrderLineItemFactory(order=order)

        with pytest.raises(ValidationError, match="Only draft orders"):
            OrderService.submit_order(order, user)


class TestOrderServiceCancelOrder:
    def test_cancel_pending_order(self):
        user = UserFactory()
        order = OrderFactory(status=OrderStatus.PENDING)

        cancelled = OrderService.cancel_order(order, user)

        assert cancelled.status == OrderStatus.CANCELLED
        assert cancelled.updated_by == user

    def test_cancel_partially_shipped_order(self):
        user = UserFactory()
        order = OrderFactory(status=OrderStatus.PARTIALLY_SHIPPED)

        cancelled = OrderService.cancel_order(order, user)

        assert cancelled.status == OrderStatus.CANCELLED

    def test_cancel_draft_order_raises(self):
        user = UserFactory()
        order = DraftOrderFactory()

        with pytest.raises(ValidationError, match="cannot be cancelled"):
            OrderService.cancel_order(order, user)

    def test_cancel_shipped_order_raises(self):
        user = UserFactory()
        order = ShippedOrderFactory()

        with pytest.raises(ValidationError, match="cannot be cancelled"):
            OrderService.cancel_order(order, user)

    def test_cancel_delivered_order_raises(self):
        user = UserFactory()
        order = DeliveredOrderFactory()

        with pytest.raises(ValidationError, match="cannot be cancelled"):
            OrderService.cancel_order(order, user)


class TestOrderServiceDeleteOrder:
    def test_delete_draft_order(self):
        order = DraftOrderFactory()

        OrderService.delete_order(order)

        order.refresh_from_db()
        assert order.is_deleted is True
        assert order.is_active is False

    def test_delete_pending_order(self):
        order = OrderFactory(status=OrderStatus.PENDING)

        OrderService.delete_order(order)

        order.refresh_from_db()
        assert order.is_deleted is True
        assert order.is_active is False

    def test_delete_non_editable_order_raises(self):
        order = ShippedOrderFactory()

        with pytest.raises(ValidationError, match="cannot be updated"):
            OrderService.delete_order(order)

    def test_delete_confirmed_order_raises(self):
        order = ConfirmedOrderFactory()

        with pytest.raises(ValidationError, match="cannot be updated"):
            OrderService.delete_order(order)
