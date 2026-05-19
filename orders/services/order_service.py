"""Business logic for order management."""

import logging
from decimal import Decimal

from django.db import transaction

from api.exceptions import ValidationError
from orders.models import Order, OrderLineItem, OrderStatus
from orders.schemas import OrderCreateSchema, OrderLineItemCreateSchema, OrderLineItemUpdateSchema, OrderUpdateSchema

logger = logging.getLogger(__name__)


class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order(payload: OrderCreateSchema, request_user, request_meta: dict) -> Order:
        order = Order.objects.create(
            customer_id=payload.customer_id,
            customer_group_id=payload.customer_group_id,
            currency=payload.currency,
            shipping_method=payload.shipping_method,
            payment_method=payload.payment_method,
            payment_gateway=payload.payment_gateway,
            billing_address_id=payload.billing_address_id,
            shipping_address_id=payload.shipping_address_id,
            email=payload.email,
            phone=payload.phone,
            customer_note=payload.customer_note,
            meta_data=payload.meta_data,
            ip_address=request_meta.get("REMOTE_ADDR"),
            user_agent=request_meta.get("HTTP_USER_AGENT"),
            created_by=request_user,
            updated_by=request_user,
        )

        subtotal = Decimal("0.00")
        for item in payload.items:
            from products.models import ProductVariant
            variant = ProductVariant.objects.get(id=item["product_variant_id"])
            quantity = item["quantity"]
            unit_price = variant.price
            item_subtotal = unit_price * quantity
            order_item = OrderLineItem.objects.create(
                order=order,
                product_variant_id=item["product_variant_id"],
                quantity=quantity,
                unit_price=unit_price,
                subtotal=item_subtotal,
                total=item_subtotal,
                created_by=request_user,
                updated_by=request_user,
            )
            subtotal += order_item.total

        order.subtotal = subtotal
        order.total = subtotal
        order.save()
        return order

    @staticmethod
    def assert_editable(order: Order) -> None:
        if order.status not in [OrderStatus.DRAFT, OrderStatus.PENDING]:
            raise ValidationError("Order cannot be updated in its current status")

    @staticmethod
    @transaction.atomic
    def update_order(order: Order, payload: OrderUpdateSchema, request_user) -> Order:
        OrderService.assert_editable(order)
        for field, value in payload.dict(exclude_unset=True).items():
            setattr(order, field, value)
        order.updated_by = request_user
        order.save()
        return order

    @staticmethod
    @transaction.atomic
    def add_item(order: Order, payload: OrderLineItemCreateSchema, request_user) -> OrderLineItem:
        OrderService.assert_editable(order)
        from products.models import ProductVariant
        variant = ProductVariant.objects.get(id=payload.product_variant_id)
        quantity = payload.quantity
        unit_price = variant.price
        item_subtotal = unit_price * quantity
        item = OrderLineItem.objects.create(
            order=order,
            product_variant_id=payload.product_variant_id,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=item_subtotal,
            total=item_subtotal,
            created_by=request_user,
            updated_by=request_user,
        )
        order.subtotal += item.total
        order.total = order.subtotal
        order.updated_by = request_user
        order.save()
        return item

    @staticmethod
    @transaction.atomic
    def update_item(order: Order, item: OrderLineItem, payload: OrderLineItemUpdateSchema, request_user) -> OrderLineItem:
        OrderService.assert_editable(order)
        old_total = item.total
        item.quantity = payload.quantity
        item.subtotal = item.unit_price * payload.quantity
        item.total = item.subtotal
        item.updated_by = request_user
        item.save()
        order.subtotal = order.subtotal - old_total + item.total
        order.total = order.subtotal
        order.updated_by = request_user
        order.save()
        return item

    @staticmethod
    @transaction.atomic
    def remove_item(order: Order, item: OrderLineItem, request_user) -> None:
        OrderService.assert_editable(order)
        item_total = item.total
        item.delete()
        order.subtotal -= item_total
        order.total = order.subtotal
        order.updated_by = request_user
        order.save()

    @staticmethod
    @transaction.atomic
    def submit_order(order: Order, request_user) -> Order:
        if order.status != OrderStatus.DRAFT:
            raise ValidationError("Only draft orders can be submitted")
        if not order.items.exists():
            raise ValidationError("Order must have at least one item")
        order.status = OrderStatus.PENDING
        order.updated_by = request_user
        order.save()
        return order

    @staticmethod
    @transaction.atomic
    def cancel_order(order: Order, request_user) -> Order:
        if order.status not in [OrderStatus.PENDING, OrderStatus.PARTIALLY_SHIPPED]:
            raise ValidationError("Order cannot be cancelled in its current status")
        order.status = OrderStatus.CANCELLED
        order.updated_by = request_user
        order.save()
        return order

    @staticmethod
    def delete_order(order: Order) -> None:
        OrderService.assert_editable(order)
        order.is_deleted = True
        order.is_active = False
        order.save(update_fields=["is_deleted", "is_active"])
