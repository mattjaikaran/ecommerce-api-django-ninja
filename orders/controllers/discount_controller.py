from django.db import models, transaction
from django.shortcuts import get_object_or_404
from ninja.pagination import paginate
from ninja_extra import (
    api_controller,
    http_delete,
    http_get,
    http_post,
    http_put,
)
from ninja_extra.permissions import IsAuthenticated

from api.decorators import handle_exceptions, log_api_call
from api.exceptions import ValidationError
from orders.models import Order, OrderDiscount
from orders.schemas import DiscountCreateSchema, DiscountSchema, DiscountUpdateSchema


@api_controller("/discounts", tags=["Order Discounts"])
class DiscountController:
    permission_classes = [IsAuthenticated]

    @http_get("", response={200: list[DiscountSchema]})
    @handle_exceptions
    @log_api_call()
    @paginate
    def list_discounts(self, request):
        """Get paginated list of discounts."""
        return OrderDiscount.objects.select_related("order").order_by("-created_at")

    @http_get("/{discount_id}", response={200: DiscountSchema})
    @handle_exceptions
    @log_api_call()
    def get_discount(self, request, discount_id: str):
        """Get single discount by ID."""
        discount = get_object_or_404(
            OrderDiscount.objects.select_related("order"), id=discount_id
        )
        return 200, discount

    @http_get("/orders/{order_id}", response={200: list[DiscountSchema]})
    @handle_exceptions
    @log_api_call()
    def get_order_discounts(self, request, order_id: str):
        """Get all discounts for a specific order."""
        order = get_object_or_404(Order, id=order_id)
        discounts = OrderDiscount.objects.filter(order=order).order_by("-created_at")
        return 200, list(discounts)

    @http_post("", response={201: DiscountSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def create_discount(self, request, payload: DiscountCreateSchema):
        """Create a new discount for an order."""
        order = get_object_or_404(Order, id=payload.order_id)

        if payload.amount > order.subtotal:
            raise ValidationError("Discount amount cannot exceed order subtotal")

        discount = OrderDiscount.objects.create(
            order=order,
            amount=payload.amount,
            notes=payload.notes,
            created_by=request.user,
        )

        # Update order discount total
        total_discounts = OrderDiscount.objects.filter(order=order).aggregate(
            total=models.Sum("amount")
        )["total"] or 0
        order.discount_amount = total_discounts
        order.total = (
            order.subtotal
            + order.shipping_amount
            + order.tax_amount
            - order.discount_amount
        )
        order.save()

        return 201, discount

    @http_put("/{discount_id}", response={200: DiscountSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def update_discount(
        self, request, discount_id: str, payload: DiscountUpdateSchema
    ):
        """Update an existing discount."""
        discount = get_object_or_404(OrderDiscount, id=discount_id)
        order = discount.order

        if payload.amount is not None:
            discount.amount = payload.amount
        if payload.notes is not None:
            discount.notes = payload.notes

        discount.updated_by = request.user
        discount.save()

        # Recalculate order discount total
        total_discounts = OrderDiscount.objects.filter(order=order).aggregate(
            total=models.Sum("amount")
        )["total"] or 0
        order.discount_amount = total_discounts
        order.total = (
            order.subtotal
            + order.shipping_amount
            + order.tax_amount
            - order.discount_amount
        )
        order.save()

        return 200, discount

    @http_delete("/{discount_id}", response={204: None})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def delete_discount(self, request, discount_id: str):
        """Delete a discount."""
        discount = get_object_or_404(OrderDiscount, id=discount_id)
        order = discount.order

        discount.is_deleted = True
        discount.save()

        # Recalculate order discount total (exclude soft-deleted)
        total_discounts = OrderDiscount.objects.filter(
            order=order, is_deleted=False
        ).aggregate(total=models.Sum("amount"))["total"] or 0
        order.discount_amount = total_discounts
        order.total = (
            order.subtotal
            + order.shipping_amount
            + order.tax_amount
            - order.discount_amount
        )
        order.save()

        return 204, None
