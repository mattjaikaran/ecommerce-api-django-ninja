from django.shortcuts import get_object_or_404
from ninja.security import django_auth
from ninja_extra import api_controller, http_delete, http_get, http_post
from ninja_jwt.authentication import JWTAuth

from api.config.error_messages import SUCCESS_MESSAGES
from api.decorators import handle_exceptions, log_api_call
from core.models import Customer
from wishlist.models import Wishlist, WishlistItem
from wishlist.schemas import (
    WishlistExistsResponseSchema,
    WishlistItemCreateSchema,
    WishlistItemSchema,
    WishlistSchema,
)
from wishlist.services import WishlistService


def _item_dict(item: WishlistItem) -> dict:
    return {
        "id": item.id,
        "product_variant_id": item.product_variant_id,
        "product_variant": {
            "id": item.product_variant.id,
            "name": item.product_variant.name,
            "sku": item.product_variant.sku,
            "price": item.product_variant.price,
        },
        "quantity": item.quantity,
        "notes": item.notes,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


@api_controller("/wishlist", tags=["Wishlist"], auth=[JWTAuth(), django_auth])
class WishlistController:
    @http_get("", response={200: WishlistSchema, 401: dict, 403: dict, 404: dict})
    @handle_exceptions()
    @log_api_call()
    def get_wishlist(self, request):
        customer = get_object_or_404(Customer, user=request.user, is_deleted=False)
        wishlist = WishlistService.get_or_create_wishlist(customer)
        items = list(wishlist.items.select_related("product_variant__product"))
        return 200, {
            "id": wishlist.id,
            "customer_id": wishlist.customer_id,
            "name": wishlist.name,
            "items": [_item_dict(item) for item in items],
            "created_at": wishlist.created_at,
            "updated_at": wishlist.updated_at,
        }

    @http_post(
        "/items",
        response={201: WishlistItemSchema, 400: dict, 401: dict, 403: dict, 404: dict},
    )
    @handle_exceptions()
    @log_api_call()
    def add_item(self, request, payload: WishlistItemCreateSchema):
        customer = get_object_or_404(Customer, user=request.user, is_deleted=False)
        wishlist = WishlistService.get_or_create_wishlist(customer)
        item = WishlistService.add_item(
            wishlist, payload.product_variant_id, payload.quantity, request.user
        )
        return 201, {
            **_item_dict(item),
            "message": SUCCESS_MESSAGES["wishlist_updated"],
        }

    @http_delete(
        "/items/{item_id}",
        response={204: None, 401: dict, 403: dict, 404: dict},
    )
    @handle_exceptions()
    @log_api_call()
    def remove_item(self, request, item_id: str):
        customer = get_object_or_404(Customer, user=request.user, is_deleted=False)
        wishlist = get_object_or_404(Wishlist, customer=customer)
        WishlistService.remove_item(wishlist, item_id, request.user)
        return 204, None

    @http_delete("", response={204: None, 401: dict, 403: dict, 404: dict})
    @handle_exceptions()
    @log_api_call()
    def clear_wishlist(self, request):
        customer = get_object_or_404(Customer, user=request.user, is_deleted=False)
        wishlist = get_object_or_404(Wishlist, customer=customer)
        WishlistService.clear(wishlist, request.user)
        return 204, None

    @http_get(
        "/items/{product_variant_id}/exists",
        response={200: WishlistExistsResponseSchema, 401: dict, 403: dict, 404: dict},
    )
    @handle_exceptions()
    @log_api_call()
    def item_exists(self, request, product_variant_id: str):
        customer = get_object_or_404(Customer, user=request.user, is_deleted=False)
        wishlist = Wishlist.objects.filter(customer=customer).first()
        exists = wishlist is not None and WishlistService.is_in_wishlist(
            wishlist, product_variant_id
        )
        return 200, {"exists": exists}
