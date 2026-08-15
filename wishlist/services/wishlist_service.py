"""Business logic for wishlist management."""

import logging
from uuid import UUID

from django.db import transaction

from api.exceptions import NotFoundError
from core.models import Customer
from products.models import ProductVariant
from wishlist.models import Wishlist, WishlistItem

logger = logging.getLogger(__name__)


class WishlistService:
    @staticmethod
    @transaction.atomic
    def get_or_create_wishlist(customer: Customer) -> Wishlist:
        wishlist, _ = Wishlist.objects.get_or_create(
            customer=customer,
            defaults={"created_by": customer.user, "updated_by": customer.user},
        )
        return wishlist

    @staticmethod
    @transaction.atomic
    def add_item(
        wishlist: Wishlist, product_variant_id: UUID, quantity: int, user
    ) -> WishlistItem:
        variant = ProductVariant.objects.filter(
            id=product_variant_id, is_deleted=False
        ).first()
        if variant is None:
            raise NotFoundError("Product variant not found")

        item = WishlistItem.objects.filter(
            wishlist=wishlist, product_variant=variant
        ).first()
        if item:
            item.quantity += quantity
            item.updated_by = user
            item.save(update_fields=["quantity", "updated_by", "updated_at"])
            return item

        return WishlistItem.objects.create(
            wishlist=wishlist,
            product_variant=variant,
            quantity=quantity,
            created_by=user,
            updated_by=user,
        )

    @staticmethod
    @transaction.atomic
    def remove_item(wishlist: Wishlist, item_id: UUID, user) -> None:
        item = WishlistItem.objects.filter(id=item_id, wishlist=wishlist).first()
        if item is None:
            raise NotFoundError("Wishlist item not found")
        item.delete()
        wishlist.updated_by = user
        wishlist.save(update_fields=["updated_by", "updated_at"])

    @staticmethod
    @transaction.atomic
    def clear(wishlist: Wishlist, user) -> None:
        WishlistItem.objects.filter(wishlist=wishlist).delete()
        wishlist.updated_by = user
        wishlist.save(update_fields=["updated_by", "updated_at"])

    @staticmethod
    def is_in_wishlist(wishlist: Wishlist, product_variant_id: UUID) -> bool:
        return WishlistItem.objects.filter(
            wishlist=wishlist, product_variant_id=product_variant_id
        ).exists()
