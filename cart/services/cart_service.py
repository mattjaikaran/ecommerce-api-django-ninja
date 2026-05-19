"""Business logic for cart management."""

import logging
from decimal import Decimal

from django.db import transaction

from api.exceptions import ValidationError
from cart.models import Cart, CartItem
from cart.schemas import CartCreateSchema, CartItemCreateSchema, CartItemUpdateSchema

logger = logging.getLogger(__name__)


class CartService:
    @staticmethod
    def update_totals(cart: Cart) -> None:
        items = cart.items.all()
        subtotal = sum(item.quantity * item.price for item in items)
        cart.subtotal = subtotal
        cart.total_price = subtotal
        cart.total_quantity = sum(item.quantity for item in items)
        cart.save()

    @staticmethod
    def create_cart(payload: CartCreateSchema, user) -> Cart:
        # Note: AbstractBaseModel.created_by is non-null. For anonymous carts,
        # a user must still be provided (e.g. a guest user record). The
        # created_by/updated_by are only set when the user is authenticated.
        create_kwargs = payload.dict()
        if user.is_authenticated:
            create_kwargs["created_by"] = user
            create_kwargs["updated_by"] = user
        else:
            # Anonymous carts require a system/guest user for created_by.
            # This path is only reachable if Cart.created_by is made nullable.
            pass
        return Cart.objects.create(**create_kwargs)

    @staticmethod
    @transaction.atomic
    def add_item(cart: Cart, payload: CartItemCreateSchema, user) -> CartItem:
        existing = cart.items.filter(product_variant_id=payload.product_variant_id).first()
        if existing:
            existing.quantity += payload.quantity
            if user.is_authenticated:
                existing.updated_by = user
            existing.save()
            cart_item = existing
        else:
            from products.models import ProductVariant
            variant = ProductVariant.objects.get(id=payload.product_variant_id)
            cart_item = CartItem.objects.create(
                cart=cart,
                product_variant_id=payload.product_variant_id,
                quantity=payload.quantity,
                price=variant.price,
                created_by=user if user.is_authenticated else None,
                updated_by=user if user.is_authenticated else None,
            )
        CartService.update_totals(cart)
        return cart_item

    @staticmethod
    @transaction.atomic
    def update_item(cart: Cart, item: CartItem, payload: CartItemUpdateSchema, user) -> CartItem:
        if payload.quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")
        item.quantity = payload.quantity
        if user.is_authenticated:
            item.updated_by = user
        item.save()
        CartService.update_totals(cart)
        return item

    @staticmethod
    @transaction.atomic
    def remove_item(cart: Cart, item: CartItem) -> None:
        item.delete()
        CartService.update_totals(cart)

    @staticmethod
    @transaction.atomic
    def clear(cart: Cart) -> Cart:
        cart.items.all().delete()
        cart.subtotal = Decimal("0.00")
        cart.total_price = Decimal("0.00")
        cart.total_quantity = 0
        cart.save()
        return cart

    @staticmethod
    @transaction.atomic
    def merge(target: Cart, source: Cart) -> Cart:
        if target.id == source.id:
            raise ValidationError("Cannot merge cart with itself")
        for source_item in source.items.all():
            existing = target.items.filter(product_variant=source_item.product_variant).first()
            if existing:
                existing.quantity += source_item.quantity
                existing.save()
            else:
                source_item.cart = target
                source_item.save()
        source.delete()
        CartService.update_totals(target)
        return target
