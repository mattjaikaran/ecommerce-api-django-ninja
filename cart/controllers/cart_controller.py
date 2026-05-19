"""Cart management controller."""

import logging
from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja_extra import api_controller, http_delete, http_get, http_post, http_put

from api.decorators import (
    create_endpoint,
    delete_endpoint,
    detail_endpoint,
    list_endpoint,
    search_and_filter,
    update_endpoint,
)
from cart.models import Cart, CartItem
from cart.schemas import (
    CartCreateSchema,
    CartItemCreateSchema,
    CartItemSchema,
    CartItemUpdateSchema,
    CartSchema,
    CartUpdateSchema,
)
from cart.services import CartService

logger = logging.getLogger(__name__)


@api_controller("/carts", tags=["Carts"])
class CartController:
    @http_get("", response={200: list[CartSchema], 401: dict, 403: dict})
    @list_endpoint(
        select_related=["customer__user"],
        prefetch_related=["items__product_variant__product"],
        search_fields=["session_key", "customer__user__username", "customer__user__email"],
        filter_fields={"is_active": "boolean", "customer_id": "exact"},
        ordering_fields=["created_at", "updated_at", "total_price"],
    )
    @search_and_filter(
        search_fields=["session_key", "customer__user__username"],
        filter_fields={"is_active": "boolean", "customer_id": "exact"},
        ordering_fields=["created_at", "updated_at"],
    )
    def list_carts(self, request):
        qs = Cart.objects.filter(is_active=True)
        if not request.user.is_staff:
            qs = qs.filter(customer__user=request.user)
        return 200, qs

    @http_get("/{cart_id}", response={200: CartSchema, 404: dict, 401: dict, 403: dict})
    @detail_endpoint(
        select_related=["customer__user"],
        prefetch_related=[
            "items__product_variant__product__category",
            "items__product_variant__options__option",
            "items__product_variant__options__value",
        ],
    )
    def get_cart(self, request, cart_id: UUID):
        kwargs = {"id": cart_id, "is_active": True}
        if request.user.is_authenticated and not request.user.is_staff:
            kwargs["customer__user"] = request.user
        cart = get_object_or_404(Cart, **kwargs)
        return 200, CartSchema.from_orm(cart)

    @http_post("", response={201: CartSchema, 400: dict, 401: dict, 403: dict})
    @create_endpoint(require_auth=False)
    def create_cart(self, request, payload: CartCreateSchema):
        cart = CartService.create_cart(payload, request.user)
        return 201, CartSchema.from_orm(cart)

    @http_put("/{cart_id}", response={200: CartSchema, 400: dict, 404: dict, 401: dict, 403: dict})
    @update_endpoint(require_auth=False)
    def update_cart(self, request, cart_id: UUID, payload: CartUpdateSchema):
        kwargs = {"id": cart_id}
        if request.user.is_authenticated and not request.user.is_staff:
            kwargs["customer__user"] = request.user
        cart = get_object_or_404(Cart, **kwargs)
        for field, value in payload.dict(exclude_unset=True).items():
            setattr(cart, field, value)
        if request.user.is_authenticated:
            cart.updated_by = request.user
        cart.save()
        return 200, CartSchema.from_orm(cart)

    @http_delete("/{cart_id}", response={204: None, 404: dict, 401: dict, 403: dict})
    @delete_endpoint(require_auth=False)
    def delete_cart(self, request, cart_id: UUID):
        cart = get_object_or_404(Cart, id=cart_id)
        cart.is_active = False
        cart.save(update_fields=["is_active"])
        return 204, None

    @http_get("/{cart_id}/items", response={200: list[CartItemSchema], 401: dict, 403: dict})
    @list_endpoint(
        require_auth=False,
        select_related=["cart", "product_variant__product"],
        prefetch_related=[
            "product_variant__options__option",
            "product_variant__options__value",
        ],
        ordering_fields=["created_at", "product_variant__name"],
    )
    def get_cart_items(self, request, cart_id: UUID):
        cart = get_object_or_404(Cart, id=cart_id, is_active=True)
        return 200, cart.items.all().order_by("created_at")

    @http_post("/{cart_id}/items", response={201: CartItemSchema, 400: dict, 404: dict, 401: dict, 403: dict})
    @create_endpoint(require_auth=False)
    def add_cart_item(self, request, cart_id: UUID, payload: CartItemCreateSchema):
        cart = get_object_or_404(Cart, id=cart_id, is_active=True)
        item = CartService.add_item(cart, payload, request.user)
        return 201, CartItemSchema.from_orm(item)

    @http_put("/{cart_id}/items/{item_id}", response={200: CartItemSchema, 400: dict, 404: dict, 401: dict, 403: dict})
    @update_endpoint(require_auth=False)
    def update_cart_item(self, request, cart_id: UUID, item_id: UUID, payload: CartItemUpdateSchema):
        cart = get_object_or_404(Cart, id=cart_id, is_active=True)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        return 200, CartItemSchema.from_orm(CartService.update_item(cart, item, payload, request.user))

    @http_delete("/{cart_id}/items/{item_id}", response={204: None, 404: dict, 401: dict, 403: dict})
    @delete_endpoint(require_auth=False)
    def remove_cart_item(self, request, cart_id: UUID, item_id: UUID):
        cart = get_object_or_404(Cart, id=cart_id, is_active=True)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        CartService.remove_item(cart, item)
        return 204, None

    @http_post("/{cart_id}/clear", response={200: CartSchema, 404: dict, 401: dict, 403: dict})
    @update_endpoint(require_auth=False)
    def clear_cart(self, request, cart_id: UUID):
        cart = get_object_or_404(Cart, id=cart_id, is_active=True)
        return 200, CartSchema.from_orm(CartService.clear(cart))

    @http_get("/session/{session_key}", response={200: CartSchema, 404: dict, 401: dict, 403: dict})
    @detail_endpoint(
        require_auth=False,
        cache_timeout=60,
        select_related=["customer__user"],
        prefetch_related=["items__product_variant__product"],
    )
    def get_cart_by_session(self, request, session_key: str):
        cart = get_object_or_404(Cart, session_key=session_key, is_active=True)
        return 200, CartSchema.from_orm(cart)

    @http_get("/customer/{customer_id}", response={200: list[CartSchema], 401: dict, 403: dict})
    @list_endpoint(
        select_related=["customer__user"],
        prefetch_related=["items__product_variant__product"],
        filter_fields={"is_active": "boolean"},
        ordering_fields=["created_at", "updated_at"],
    )
    def get_customer_carts(self, request, customer_id: UUID):
        return 200, Cart.objects.filter(customer_id=customer_id, is_active=True)

    @http_post("/{cart_id}/merge/{source_cart_id}", response={200: CartSchema, 400: dict, 404: dict, 401: dict, 403: dict})
    @update_endpoint(require_auth=False)
    def merge_carts(self, request, cart_id: UUID, source_cart_id: UUID):
        target = get_object_or_404(Cart, id=cart_id, is_active=True)
        source = get_object_or_404(Cart, id=source_cart_id, is_active=True)
        return 200, CartSchema.from_orm(CartService.merge(target, source))
