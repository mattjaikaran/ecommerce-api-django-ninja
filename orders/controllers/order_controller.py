"""Order management controller."""

import logging

from django.shortcuts import get_object_or_404
from ninja_extra import (
    api_controller,
    http_delete,
    http_get,
    http_post,
    http_put,
)

from api.decorators import (
    create_endpoint,
    delete_endpoint,
    detail_endpoint,
    list_endpoint,
    search_and_filter,
    update_endpoint,
)
from orders.models import Order, OrderLineItem
from orders.schemas import (
    OrderCreateSchema,
    OrderHistorySchema,
    OrderLineItemCreateSchema,
    OrderLineItemSchema,
    OrderLineItemUpdateSchema,
    OrderSchema,
    OrderUpdateSchema,
)
from orders.services import OrderService

logger = logging.getLogger(__name__)


@api_controller("/orders", tags=["Orders"])
class OrderController:
    @http_get("", response={200: list[OrderSchema], 401: dict, 403: dict})
    @list_endpoint(
        select_related=["customer", "customer_group", "billing_address", "shipping_address"],
        prefetch_related=[
            "items__product_variant__product",
            "fulfillments",
            "transactions",
            "refunds",
            "taxes",
            "notes",
            "history",
        ],
        search_fields=["order_number", "email", "customer__user__username"],
        filter_fields={
            "status": "exact",
            "payment_status": "exact",
            "customer_id": "exact",
        },
        ordering_fields=["created_at", "order_number", "total", "status"],
    )
    @search_and_filter(
        search_fields=["order_number", "email", "customer__user__username"],
        filter_fields={"status": "exact", "payment_status": "exact"},
        ordering_fields=["created_at", "order_number", "total"],
    )
    def list_orders(self, request):
        qs = Order.objects.all()
        if not request.user.is_staff:
            qs = qs.filter(customer__user=request.user)
        return 200, qs

    @http_get("/{order_id}", response={200: OrderSchema, 401: dict, 403: dict, 404: dict})
    @detail_endpoint(
        select_related=["customer__user", "billing_address", "shipping_address", "customer_group"],
        prefetch_related=["items__product_variant__product", "history", "notes"],
    )
    def get_order(self, request, order_id: str):
        kwargs = {"id": order_id}
        if not request.user.is_staff:
            kwargs["customer__user"] = request.user
        order = get_object_or_404(Order, **kwargs)
        return 200, order

    @http_post("", response={201: OrderSchema, 400: dict, 401: dict, 403: dict, 404: dict, 409: dict})
    @create_endpoint()
    def create_order(self, request, payload: OrderCreateSchema):
        order = OrderService.create_order(payload, request.user, request.META)
        return 201, order

    @http_put("/{order_id}", response={200: OrderSchema, 400: dict, 401: dict, 403: dict, 404: dict})
    @update_endpoint()
    def update_order(self, request, order_id: str, payload: OrderUpdateSchema):
        order = get_object_or_404(Order, id=order_id)
        if payload.status is not None and not request.user.is_staff:
            from api.exceptions import APIPermissionError
            raise APIPermissionError("Only admins can update order status")
        return 200, OrderService.update_order(order, payload, request.user)

    @http_delete("/{order_id}", response={204: None, 400: dict, 401: dict, 403: dict, 404: dict})
    @delete_endpoint()
    def delete_order(self, request, order_id: str):
        order = get_object_or_404(Order, id=order_id)
        OrderService.delete_order(order)
        return 204, None

    @http_post("/{order_id}/items", response={201: OrderLineItemSchema, 400: dict, 404: dict})
    @create_endpoint()
    def add_order_item(self, request, order_id: str, payload: OrderLineItemCreateSchema):
        order = get_object_or_404(Order, id=order_id)
        item = OrderService.add_item(order, payload, request.user)
        return 201, item

    @http_put("/{order_id}/items/{item_id}", response={200: OrderLineItemSchema, 400: dict, 404: dict})
    @update_endpoint()
    def update_order_item(self, request, order_id: str, item_id: str, payload: OrderLineItemUpdateSchema):
        order = get_object_or_404(Order, id=order_id)
        item = get_object_or_404(OrderLineItem, id=item_id, order=order)
        return 200, OrderService.update_item(order, item, payload, request.user)

    @http_delete("/{order_id}/items/{item_id}", response={204: None, 404: dict})
    @delete_endpoint()
    def delete_order_item(self, request, order_id: str, item_id: str):
        order = get_object_or_404(Order, id=order_id)
        item = get_object_or_404(OrderLineItem, id=item_id, order=order)
        OrderService.remove_item(order, item, request.user)
        return 204, None

    @http_post("/{order_id}/submit", response={200: OrderSchema, 400: dict, 404: dict})
    @update_endpoint()
    def submit_order(self, request, order_id: str):
        order = get_object_or_404(Order, id=order_id)
        return 200, OrderService.submit_order(order, request.user)

    @http_post("/{order_id}/cancel", response={200: OrderSchema, 400: dict, 404: dict})
    @update_endpoint()
    def cancel_order(self, request, order_id: str):
        order = get_object_or_404(Order, id=order_id)
        return 200, OrderService.cancel_order(order, request.user)

    @http_get("/{order_id}/history", response={200: list[OrderHistorySchema], 401: dict, 403: dict, 404: dict})
    @list_endpoint(
        select_related=["order", "created_by"],
        ordering_fields=["created_at"],
    )
    def get_order_history(self, request, order_id: str):
        order = get_object_or_404(Order, id=order_id)
        return 200, order.history.all().order_by("-created_at")

    @http_get("/search", response={200: list[OrderSchema], 401: dict, 403: dict})
    @list_endpoint(
        select_related=["customer", "customer_group", "billing_address", "shipping_address"],
        prefetch_related=[
            "items__product_variant__product",
            "fulfillments",
            "transactions",
            "refunds",
            "taxes",
            "notes",
            "history",
        ],
        search_fields=["order_number", "email", "customer__user__username"],
        filter_fields={"status": "exact", "payment_status": "exact"},
        ordering_fields=["created_at", "order_number", "total"],
    )
    @search_and_filter(
        search_fields=["order_number", "email", "customer__user__username"],
        filter_fields={"status": "exact", "payment_status": "exact"},
        ordering_fields=["created_at", "order_number", "total"],
    )
    def search_orders(self, request):
        return 200, Order.objects.all()
