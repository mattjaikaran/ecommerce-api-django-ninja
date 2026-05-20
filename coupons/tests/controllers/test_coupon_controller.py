"""Tests for CouponController HTTP endpoints."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.test import Client
from django.utils import timezone

from coupons.models import Coupon
from coupons.models.choices import DiscountType
from coupons.tests.factories.coupon_factory import CouponFactory, CouponUsageFactory
from core.tests.factories import CustomerFactory, UserFactory
from orders.tests.factories import OrderFactory

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


def _valid_coupon_payload():
    now = timezone.now()
    return {
        "code": "TESTCODE",
        "discount_type": DiscountType.PERCENTAGE,
        "discount_value": "10.00",
        "valid_from": now.isoformat(),
        "valid_to": (now + timedelta(days=30)).isoformat(),
        "is_active": True,
    }


class TestCouponListEndpoint:
    def test_list_requires_auth(self, client):
        response = client.get("/api/coupons")
        assert response.status_code in (401, 403)

    def test_list_returns_coupons(self, auth_client):
        c, user = auth_client
        CouponFactory.create_batch(3)

        response = c.get("/api/coupons")

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) >= 3

    def test_list_filter_active(self, auth_client):
        c, _ = auth_client
        active = CouponFactory(is_active=True)
        inactive = CouponFactory(is_active=False)

        response = c.get("/api/coupons?is_active=true")

        assert response.status_code == 200
        data = response.json()
        ids = [item["id"] for item in data["results"]]
        assert str(active.id) in ids
        assert str(inactive.id) not in ids

    def test_list_filter_inactive(self, auth_client):
        c, _ = auth_client
        inactive = CouponFactory(is_active=False)
        active = CouponFactory(is_active=True)

        response = c.get("/api/coupons?is_active=false")

        assert response.status_code == 200
        data = response.json()
        ids = [item["id"] for item in data["results"]]
        assert str(inactive.id) in ids
        assert str(active.id) not in ids

    def test_list_excludes_deleted(self, auth_client):
        c, _ = auth_client
        deleted = CouponFactory(is_deleted=True)
        active = CouponFactory()

        response = c.get("/api/coupons")

        assert response.status_code == 200
        data = response.json()
        ids = [item["id"] for item in data["results"]]
        assert str(deleted.id) not in ids
        assert str(active.id) in ids


class TestCouponDetailEndpoint:
    def test_get_coupon_returns_200(self, auth_client):
        c, _ = auth_client
        coupon = CouponFactory()

        response = c.get(f"/api/coupons/{coupon.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(coupon.id)
        assert data["code"] == coupon.code

    def test_get_nonexistent_coupon_returns_404(self, auth_client):
        import uuid
        c, _ = auth_client

        response = c.get(f"/api/coupons/{uuid.uuid4()}")

        assert response.status_code == 404

    def test_get_deleted_coupon_returns_404(self, auth_client):
        c, _ = auth_client
        coupon = CouponFactory(is_deleted=True)

        response = c.get(f"/api/coupons/{coupon.id}")

        assert response.status_code == 404

    def test_get_requires_auth(self, client):
        coupon = CouponFactory()

        response = client.get(f"/api/coupons/{coupon.id}")

        assert response.status_code in (401, 403)


class TestCouponCreateEndpoint:
    def test_create_requires_auth(self, client):
        response = client.post(
            "/api/coupons",
            data=_valid_coupon_payload(),
            content_type="application/json",
        )
        assert response.status_code in (401, 403)

    def test_create_coupon_returns_201(self, auth_client):
        c, user = auth_client
        payload = _valid_coupon_payload()

        response = c.post("/api/coupons", data=payload, content_type="application/json")

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "TESTCODE"
        assert Coupon.objects.filter(code="TESTCODE").exists()

    def test_create_normalizes_code_to_upper(self, auth_client):
        c, _ = auth_client
        payload = {**_valid_coupon_payload(), "code": "lowercase"}

        response = c.post("/api/coupons", data=payload, content_type="application/json")

        assert response.status_code == 201
        assert Coupon.objects.filter(code="LOWERCASE").exists()

    def test_create_duplicate_code_returns_error(self, auth_client):
        c, _ = auth_client
        CouponFactory(code="DUPE")
        payload = {**_valid_coupon_payload(), "code": "DUPE"}

        response = c.post("/api/coupons", data=payload, content_type="application/json")

        assert response.status_code in (400, 409, 422)


class TestCouponUpdateEndpoint:
    def test_update_coupon_returns_200(self, auth_client):
        c, user = auth_client
        coupon = CouponFactory(created_by=user)

        response = c.put(
            f"/api/coupons/{coupon.id}",
            data={"is_active": False},
            content_type="application/json",
        )

        assert response.status_code == 200
        coupon.refresh_from_db()
        assert coupon.is_active is False

    def test_update_nonexistent_coupon_returns_404(self, auth_client):
        import uuid
        c, _ = auth_client

        response = c.put(
            f"/api/coupons/{uuid.uuid4()}",
            data={"is_active": False},
            content_type="application/json",
        )

        assert response.status_code == 404

    def test_update_requires_auth(self, client):
        coupon = CouponFactory()

        response = client.put(
            f"/api/coupons/{coupon.id}",
            data={"is_active": False},
            content_type="application/json",
        )

        assert response.status_code in (401, 403)


class TestCouponDeleteEndpoint:
    def test_delete_coupon_returns_204(self, auth_client):
        c, _ = auth_client
        coupon = CouponFactory()

        response = c.delete(f"/api/coupons/{coupon.id}")

        assert response.status_code == 204

    def test_delete_soft_deletes(self, auth_client):
        c, _ = auth_client
        coupon = CouponFactory()

        c.delete(f"/api/coupons/{coupon.id}")

        coupon.refresh_from_db()
        assert coupon.is_deleted is True
        assert coupon.is_active is False

    def test_delete_nonexistent_returns_404(self, auth_client):
        import uuid
        c, _ = auth_client

        response = c.delete(f"/api/coupons/{uuid.uuid4()}")

        assert response.status_code == 404

    def test_delete_requires_auth(self, client):
        coupon = CouponFactory()

        response = client.delete(f"/api/coupons/{coupon.id}")

        assert response.status_code in (401, 403)


class TestCouponValidateEndpoint:
    def test_validate_valid_coupon(self, auth_client, customer):
        c, _ = auth_client
        coupon = CouponFactory(min_order_amount=Decimal("0"))

        response = c.post(
            "/api/coupons/validate",
            data={"code": coupon.code, "order_subtotal": "100.00"},
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert Decimal(data["discount_amount"]) > 0

    def test_validate_inactive_coupon_returns_invalid(self, auth_client, customer):
        c, _ = auth_client
        coupon = CouponFactory(is_active=False)

        response = c.post(
            "/api/coupons/validate",
            data={"code": coupon.code, "order_subtotal": "100.00"},
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    def test_validate_expired_coupon_returns_invalid(self, auth_client, customer):
        c, _ = auth_client
        coupon = CouponFactory(
            valid_from=timezone.now() - timedelta(days=60),
            valid_to=timezone.now() - timedelta(days=1),
        )

        response = c.post(
            "/api/coupons/validate",
            data={"code": coupon.code, "order_subtotal": "100.00"},
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    def test_validate_requires_auth(self, client):
        response = client.post(
            "/api/coupons/validate",
            data={"code": "ANYCOUPON", "order_subtotal": "100.00"},
            content_type="application/json",
        )
        assert response.status_code in (401, 403)
