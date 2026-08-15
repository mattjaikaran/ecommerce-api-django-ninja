"""Tests for WishlistService business logic."""

from uuid import uuid4

import pytest

from api.exceptions import NotFoundError
from core.tests.factories import CustomerFactory
from products.tests.factories import ProductVariantFactory
from wishlist.models import Wishlist, WishlistItem
from wishlist.services import WishlistService
from wishlist.tests.factories.wishlist_factory import (
    WishlistFactory,
    WishlistItemFactory,
)

pytestmark = pytest.mark.django_db


class TestGetOrCreateWishlist:
    def test_creates_once_and_returns_same(self):
        customer = CustomerFactory()
        first = WishlistService.get_or_create_wishlist(customer)
        second = WishlistService.get_or_create_wishlist(customer)
        assert first.id == second.id
        assert Wishlist.objects.filter(customer=customer).count() == 1
        assert first.created_by == customer.user
        assert first.updated_by == customer.user

    def test_returns_existing_wishlist(self):
        customer = CustomerFactory()
        existing = WishlistFactory(customer=customer)
        got = WishlistService.get_or_create_wishlist(customer)
        assert got.id == existing.id
        assert Wishlist.objects.count() == 1


class TestAddItem:
    def test_adds_new_item(self):
        customer = CustomerFactory()
        wishlist = WishlistService.get_or_create_wishlist(customer)
        variant = ProductVariantFactory()
        item = WishlistService.add_item(wishlist, variant.id, 2, customer.user)
        assert item.wishlist == wishlist
        assert item.product_variant == variant
        assert item.quantity == 2
        assert item.created_by == customer.user

    def test_add_same_variant_bumps_quantity(self):
        customer = CustomerFactory()
        wishlist = WishlistFactory(customer=customer)
        variant = ProductVariantFactory()
        WishlistItemFactory(wishlist=wishlist, product_variant=variant, quantity=1)
        item = WishlistService.add_item(wishlist, variant.id, 3, customer.user)
        assert item.quantity == 4
        assert WishlistItem.objects.filter(wishlist=wishlist).count() == 1

    def test_add_unknown_variant_raises_not_found(self):
        customer = CustomerFactory()
        wishlist = WishlistService.get_or_create_wishlist(customer)
        with pytest.raises(NotFoundError):
            WishlistService.add_item(wishlist, uuid4(), 1, customer.user)


class TestRemoveItem:
    def test_removes_own_item(self):
        customer = CustomerFactory()
        wishlist = WishlistFactory(customer=customer)
        item = WishlistItemFactory(wishlist=wishlist)
        WishlistService.remove_item(wishlist, item.id, customer.user)
        assert not WishlistItem.objects.filter(id=item.id).exists()

    def test_remove_foreign_item_raises_not_found(self):
        owner = CustomerFactory()
        other = CustomerFactory()
        owner_wishlist = WishlistFactory(customer=owner)
        other_wishlist = WishlistFactory(customer=other)
        foreign_item = WishlistItemFactory(wishlist=other_wishlist)
        with pytest.raises(NotFoundError):
            WishlistService.remove_item(owner_wishlist, foreign_item.id, owner.user)
        assert WishlistItem.objects.filter(id=foreign_item.id).exists()


class TestClear:
    def test_clears_all_items(self):
        customer = CustomerFactory()
        wishlist = WishlistFactory(customer=customer)
        WishlistItemFactory.create_batch(wishlist=wishlist, size=3)
        WishlistService.clear(wishlist, customer.user)
        assert WishlistItem.objects.filter(wishlist=wishlist).count() == 0


class TestIsInWishlist:
    def test_returns_true_when_present(self):
        customer = CustomerFactory()
        wishlist = WishlistFactory(customer=customer)
        variant = ProductVariantFactory()
        WishlistItemFactory(wishlist=wishlist, product_variant=variant)
        assert WishlistService.is_in_wishlist(wishlist, variant.id) is True

    def test_returns_false_when_absent(self):
        customer = CustomerFactory()
        wishlist = WishlistFactory(customer=customer)
        variant = ProductVariantFactory()
        assert WishlistService.is_in_wishlist(wishlist, variant.id) is False
