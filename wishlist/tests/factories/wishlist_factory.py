"""Factories for Wishlist and WishlistItem models."""

import factory

from core.tests.factories import CustomerFactory
from products.tests.factories import ProductVariantFactory
from wishlist.models import Wishlist, WishlistItem


class WishlistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Wishlist

    customer = factory.SubFactory(CustomerFactory)
    name = None
    created_by = factory.SelfAttribute("customer.user")
    updated_by = factory.SelfAttribute("customer.user")


class WishlistItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WishlistItem

    wishlist = factory.SubFactory(WishlistFactory)
    product_variant = factory.SubFactory(ProductVariantFactory)
    quantity = 1
    notes = None
    created_by = factory.SelfAttribute("wishlist.customer.user")
    updated_by = factory.SelfAttribute("wishlist.customer.user")
