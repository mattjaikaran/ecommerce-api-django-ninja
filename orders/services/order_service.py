"""Business logic for order management."""

import hashlib
import logging
import uuid
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from api.config.constants import IDEMPOTENCY_KEY_TTL_HOURS
from api.exceptions import ConflictError, NotFoundError, ValidationError
from core.models import Customer
from loyalty.tasks import credit_order_points
from orders.models import (
    IdempotencyKey,
    Order,
    OrderHistory,
    OrderLineItem,
    OrderStatus,
)
from orders.models.choices import ORDER_STATUS_TRANSITIONS
from orders.schemas import (
    OrderCreateSchema,
    OrderLineItemCreateSchema,
    OrderLineItemUpdateSchema,
    OrderUpdateSchema,
)

logger = logging.getLogger(__name__)


class OrderService:
    @staticmethod
    def _hash_idempotency_key(key: str) -> str:
        """Return the SHA-256 hash of an idempotency key."""
        return hashlib.sha256(key.encode()).hexdigest()

    @staticmethod
    def _hash_request_payload(payload: OrderCreateSchema) -> str:
        """Return a canonical hash of the request payload."""
        return hashlib.sha256(payload.model_dump_json().encode()).hexdigest()

    @staticmethod
    def _assert_customer_owned(payload: OrderCreateSchema, request_user) -> None:
        """Raise 404 unless the customer belongs to the request user (or staff)."""
        if request_user.is_staff:
            return
        owned = Customer.objects.filter(id=payload.customer_id, user=request_user).exists()
        if not owned:
            raise NotFoundError("Customer not found")

    @staticmethod
    @transaction.atomic
    def create_order(
        payload: OrderCreateSchema,
        request_user,
        request_meta: dict,
        idempotency_key: str | None = None,
    ) -> tuple[Order, bool]:
        """Create an order, honoring an optional idempotency key.

        Returns (order, created). When an idempotency key is supplied and
        the same key was already used with the same payload, the original
        order is returned with created=False. Reusing a key with a
        different payload raises ConflictError.
        """
        OrderService._assert_customer_owned(payload, request_user)

        if idempotency_key:
            key_hash = OrderService._hash_idempotency_key(idempotency_key)
            request_hash = OrderService._hash_request_payload(payload)

            # An expired claim is reusable: drop it before claiming.
            IdempotencyKey.objects.filter(
                key_hash=key_hash,
                user=request_user,
                expires_at__lte=timezone.now(),
            ).delete()

            # get_or_create is race-safe under the unique (key_hash, user)
            # constraint: the losing concurrent request catches IntegrityError
            # internally, re-fetches, and returns the winner's record.
            key_record, key_created = IdempotencyKey.objects.get_or_create(
                key_hash=key_hash,
                user=request_user,
                defaults={
                    "request_hash": request_hash,
                    "expires_at": timezone.now()
                    + timedelta(hours=IDEMPOTENCY_KEY_TTL_HOURS),
                },
            )

            if not key_created:
                if key_record.request_hash != request_hash:
                    raise ConflictError(
                        "Idempotency key reused with a different payload"
                    )
                if key_record.order_id is None:
                    # A request is in flight but the order does not exist
                    # yet. Return the key so the caller can retry after a
                    # short delay.
                    raise ConflictError(
                        "Request with this idempotency key is in progress"
                    )
                return key_record.order, False

            order = OrderService._create_order(
                payload, request_user, request_meta
            )
            key_record.order = order
            key_record.save(update_fields=["order", "updated_at"])
            return order, True

        order = OrderService._create_order(payload, request_user, request_meta)
        return order, True

    @staticmethod
    def _generate_order_number() -> str:
        """Return a unique, human-readable order number."""
        date_part = timezone.now().strftime("%Y%m%d")
        return f"ORD-{date_part}-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def _create_order(payload: OrderCreateSchema, request_user, request_meta: dict) -> Order:
        order = Order.objects.create(
            order_number=OrderService._generate_order_number(),
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
    def transition_order(
        order: Order,
        new_status: str,
        request_user,
        notes: str | None = None,
        force: bool = False,
    ) -> Order:
        """Transition an order to a new status, enforcing the state machine.

        Rejects transitions not in ORDER_STATUS_TRANSITIONS with a 409
        ConflictError unless force is True (staff override). Records an
        OrderHistory entry for every transition.
        """
        if new_status == order.status:
            return order
        allowed = ORDER_STATUS_TRANSITIONS.get(order.status, set())
        if not force and new_status not in allowed:
            message = (
                f"Order cannot transition from {order.status} to {new_status}"
            )
            raise ConflictError(message)
        old_status = order.status
        order.status = new_status
        order.updated_by = request_user
        order.save(update_fields=["status", "updated_by", "updated_at"])
        OrderHistory.objects.create(
            order=order,
            status=new_status,
            old_status=old_status,
            notes=notes,
            created_by=request_user,
        )
        if new_status == OrderStatus.COMPLETED:
            credit_order_points.delay(order.id)
        return order

    @staticmethod
    @transaction.atomic
    def update_order(order: Order, payload: OrderUpdateSchema, request_user) -> Order:
        OrderService.assert_editable(order)
        updates = payload.dict(exclude_unset=True)
        new_status = updates.pop("status", None)
        if new_status is not None and new_status != order.status:
            OrderService.transition_order(
                order,
                new_status,
                request_user,
                notes="Status updated via order update",
                force=request_user.is_staff,
            )
        for field, value in updates.items():
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
        if not order.items.exists():
            raise ValidationError("Order must have at least one item")
        return OrderService.transition_order(
            order,
            OrderStatus.PENDING,
            request_user,
            notes="Order submitted",
        )

    @staticmethod
    @transaction.atomic
    def cancel_order(order: Order, request_user) -> Order:
        return OrderService.transition_order(
            order,
            OrderStatus.CANCELLED,
            request_user,
            notes="Order cancelled",
        )

    @staticmethod
    def delete_order(order: Order) -> None:
        OrderService.assert_editable(order)
        order.is_deleted = True
        order.is_active = False
        order.save(update_fields=["is_deleted", "is_active"])
