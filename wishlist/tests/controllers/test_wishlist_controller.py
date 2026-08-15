"""Tests for WishlistController HTTP endpoints."""

from uuid import uuid4

import pytest
from django.test import Client

from api.config.error_messages import SUCCESS_MESSAGES
from core.tests.factories import CustomerFactory, UserFactory
from products.tests.factories import ProductVariantFactory
from wishlist.models import Wishlist, WishlistItem
from wishlist.tests.factories.wishlist_factory import (
    WishlistFactory,
    WishlistItemFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def customer(user):
    return CustomerFactory(user=user)


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client, user


class TestGetWishlistEndpoint:
    def test_get_requires_auth(self, client):
        response = client.get("/api/wishlist")
        assert response.status_code in (401, 403)

    def test_get_returns_own_wishlist_with_items(self, auth_client, customer):
        c, _ = auth_client
        wishlist = WishlistFactory(customer=customer)
        variant = ProductVariantFactory()
        WishlistItemFactory(wishlist=wishlist, product_variant=variant, quantity=2)

        response = c.get("/api/wishlist")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(wishlist.id)
        assert data["customer_id"] == str(customer.id)
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["product_variant_id"] == str(variant.id)
        assert item["quantity"] == 2
        assert item["product_variant"]["id"] == str(variant.id)
        assert item["product_variant"]["name"] == variant.name
        assert item["product_variant"]["sku"] == variant.sku
        assert str(item["product_variant"]["price"]) == str(variant.price)

    def test_get_creates_wishlist_lazily(self, auth_client, customer):
        c, _ = auth_client
        response = c.get("/api/wishlist")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert Wishlist.objects.filter(customer=customer).exists()

    def test_get_does_not_leak_other_users_items(self, auth_client, customer):
        c, _ = auth_client
        other = CustomerFactory()
        other_wishlist = WishlistFactory(customer=other)
        WishlistItemFactory(wishlist=other_wishlist)

        response = c.get("/api/wishlist")

        assert response.status_code == 200
        data = response.json()
        assert data["customer_id"] == str(customer.id)
        assert data["items"] == []


class TestAddItemEndpoint:
    def test_add_requires_auth(self, client):
        response = client.post(
            "/api/wishlist/items",
            data={"product_variant_id": str(uuid4()), "quantity": 1},
            content_type="application/json",
        )
        assert response.status_code in (401, 403)

    def test_add_item_returns_201_with_message(self, auth_client, customer):
        c, _ = auth_client
        variant = ProductVariantFactory()

        response = c.post(
            "/api/wishlist/items",
            data={"product_variant_id": str(variant.id), "quantity": 2},
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["product_variant_id"] == str(variant.id)
        assert data["quantity"] == 2
        assert data["product_variant"]["sku"] == variant.sku
        assert data["message"] == SUCCESS_MESSAGES["wishlist_updated"]
        assert Wishlist.objects.filter(customer=customer).exists()

    def test_add_duplicate_bumps_quantity(self, auth_client, customer):
        c, _ = auth_client
        wishlist = WishlistFactory(customer=customer)
        variant = ProductVariantFactory()
        WishlistItemFactory(wishlist=wishlist, product_variant=variant, quantity=1)

        response = c.post(
            "/api/wishlist/items",
            data={"product_variant_id": str(variant.id), "quantity": 2},
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["quantity"] == 3
        assert WishlistItem.objects.filter(wishlist=wishlist).count() == 1

    def test_add_unknown_variant_returns_404(self, auth_client):
        c, _ = auth_client
        response = c.post(
            "/api/wishlist/items",
            data={"product_variant_id": str(uuid4()), "quantity": 1},
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_add_invalid_quantity_returns_400(self, auth_client):
        c, _ = auth_client
        variant = ProductVariantFactory()
        response = c.post(
            "/api/wishlist/items",
            data={"product_variant_id": str(variant.id), "quantity": 0},
            content_type="application/json",
        )
        assert response.status_code == 422


class TestRemoveItemEndpoint:
    def test_remove_requires_auth(self, client):
        response = client.delete(f"/api/wishlist/items/{uuid4()}")
        assert response.status_code in (401, 403)

    def test_remove_item_returns_204(self, auth_client, customer):
        c, _ = auth_client
        wishlist = WishlistFactory(customer=customer)
        item = WishlistItemFactory(wishlist=wishlist)

        response = c.delete(f"/api/wishlist/items/{item.id}")

        assert response.status_code == 204
        assert not WishlistItem.objects.filter(id=item.id).exists()

    def test_remove_foreign_item_returns_404(self, auth_client, customer):
        c, _ = auth_client
        own_wishlist = WishlistFactory(customer=customer)
        other = CustomerFactory()
        other_wishlist = WishlistFactory(customer=other)
        foreign_item = WishlistItemFactory(wishlist=other_wishlist)

        response = c.delete(f"/api/wishlist/items/{foreign_item.id}")

        assert response.status_code == 404
        assert WishlistItem.objects.filter(id=foreign_item.id).exists()
        assert WishlistItem.objects.filter(wishlist=own_wishlist).count() == 0

    def test_remove_item_not_in_own_wishlist_returns_404(self, auth_client, customer):
        c, _ = auth_client
        WishlistFactory(customer=customer)
        foreign_item = WishlistItemFactory()

        response = c.delete(f"/api/wishlist/items/{foreign_item.id}")

        assert response.status_code == 404


class TestClearWishlistEndpoint:
    def test_clear_requires_auth(self, client):
        response = client.delete("/api/wishlist")
        assert response.status_code in (401, 403)

    def test_clear_returns_204(self, auth_client, customer):
        c, _ = auth_client
        wishlist = WishlistFactory(customer=customer)
        WishlistItemFactory.create_batch(wishlist=wishlist, size=3)

        response = c.delete("/api/wishlist")

        assert response.status_code == 204
        assert WishlistItem.objects.filter(wishlist=wishlist).count() == 0

    def test_clear_without_wishlist_returns_404(self, auth_client):
        c, _ = auth_client
        response = c.delete("/api/wishlist")
        assert response.status_code == 404


class TestExistsEndpoint:
    def test_exists_requires_auth(self, client):
        response = client.get(f"/api/wishlist/items/{uuid4()}/exists")
        assert response.status_code in (401, 403)

    def test_exists_returns_true(self, auth_client, customer):
        c, _ = auth_client
        wishlist = WishlistFactory(customer=customer)
        variant = ProductVariantFactory()
        WishlistItemFactory(wishlist=wishlist, product_variant=variant)

        response = c.get(f"/api/wishlist/items/{variant.id}/exists")

        assert response.status_code == 200
        assert response.json() == {"exists": True}

    def test_exists_returns_false(self, auth_client, customer):
        c, _ = auth_client
        WishlistFactory(customer=customer)
        variant = ProductVariantFactory()

        response = c.get(f"/api/wishlist/items/{variant.id}/exists")

        assert response.status_code == 200
        assert response.json() == {"exists": False}

    def test_exists_returns_false_without_wishlist(self, auth_client, customer):
        c, _ = auth_client
        variant = ProductVariantFactory()
        assert Wishlist.objects.filter(customer=customer).count() == 0

        response = c.get(f"/api/wishlist/items/{variant.id}/exists")
        assert response.status_code == 200
        assert response.json() == {"exists": False}
