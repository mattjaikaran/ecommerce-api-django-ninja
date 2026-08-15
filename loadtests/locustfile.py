"""Locust load-test suite for the ecommerce API.

Run from the repo root against the running dev stack:

    uv run locust --headless -u 20 -r 2 -t 5m --host http://localhost:8000 \
        -f loadtests/locustfile.py --csv loadtests/results/run1

The suite seeds its own catalog (one category, 25 active products, one or
two variants each) and mints a Django session + JWT per simulated shopper,
so the product, cart, and order endpoints all see an authenticated user.
"""

import os
import uuid
from decimal import Decimal
from importlib import import_module
from random import choice, randint

import locust  # noqa: F401 — imported first so gevent patch_all runs before Django loads

# Bootstrap Django after locust (gevent) is imported. The dev stack runs
# PostgreSQL and Redis in Docker; DB_PASSWORD is forced because the host
# .env ships an empty value while the compose container uses "postgres".
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings.dev")
os.environ["DB_PASSWORD"] = "postgres"
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_USER", "mattjaikaran")
os.environ.setdefault("DB_NAME", "ecommerce_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

import django

django.setup()

from django.conf import settings  # noqa: E402
from locust import HttpUser, between, task  # noqa: E402
from ninja_jwt.tokens import RefreshToken  # noqa: E402

from core.models import Address, Customer, User  # noqa: E402
from products.models import Product, ProductCategory, ProductVariant  # noqa: E402
from products.models.choices import ProductStatus  # noqa: E402

SEED_EMAIL = "loadtest.seed@example.com"
SEED_PASSWORD = "loadtest-seed-password"
CATALOG_SIZE = 25


def _seed_catalog(seed_user):
    """Create the shared category and catalog (idempotent, capped at 25)."""
    category, _ = ProductCategory.objects.get_or_create(
        slug="loadtest-category",
        defaults={
            "name": "Load Test",
            "description": "Catalog seeded by the locust suite",
            "position": 0,
            "created_by": seed_user,
            "updated_by": seed_user,
        },
    )
    existing = Product.objects.filter(category=category).count()
    for index in range(existing, CATALOG_SIZE):
        suffix = uuid.uuid4().hex[:8]
        product, created = Product.objects.get_or_create(
            slug=f"loadtest-product-{suffix}",
            defaults={
                "name": f"Load Test Product {index:02d}",
                "description": "Seeded catalog item",
                "category": category,
                "price": Decimal("49.99"),
                "quantity": 100,
                "status": ProductStatus.ACTIVE,
                "is_active": True,
                "featured": False,
                "created_by": seed_user,
                "updated_by": seed_user,
            },
        )
        if created:
            variant_count = 2 if index % 2 else 1
            for variant_index in range(variant_count):
                ProductVariant.objects.get_or_create(
                    sku=f"LT-{uuid.uuid4().hex[:8]}",
                    defaults={
                        "product": product,
                        "name": f"Variant {variant_index}",
                        "price": product.price,
                        "inventory_quantity": 100,
                        "is_active": True,
                        "created_by": seed_user,
                        "updated_by": seed_user,
                    },
                )


def _seed():
    """Create the seed user and catalog, returning the seed user."""
    seed_user, created = User.objects.get_or_create(
        email=SEED_EMAIL,
        defaults={
            "username": "loadtest-seed",
            "first_name": "Load",
            "last_name": "Test",
            "is_staff": True,
        },
    )
    if created or not seed_user.password:
        seed_user.set_password(SEED_PASSWORD)
        seed_user.save()
    _seed_catalog(seed_user)
    return seed_user


_seed()
PRODUCT_IDS = [
    str(row)
    for row in Product.objects.filter(is_active=True).values_list("id", flat=True)
]
VARIANT_IDS = [
    str(row)
    for row in ProductVariant.objects.filter(is_active=True).values_list(
        "id", flat=True
    )
]
assert PRODUCT_IDS, "Catalog seeding produced no products"
assert VARIANT_IDS, "Catalog seeding produced no product variants"


def _session_cookie(user):
    """Return a sessionid cookie that authenticates the request as `user`.

    Uses the configured session engine (cache-backed in dev), so the server
    finds the session in Redis when it resolves the cookie.
    """
    engine = import_module(settings.SESSION_ENGINE)
    session = engine.SessionStore()
    session["_auth_user_id"] = str(user.pk)
    session["_auth_user_backend"] = "django.contrib.auth.backends.ModelBackend"
    session["_auth_user_hash"] = user.get_session_auth_hash()
    session.create()
    return f"sessionid={session.session_key}"


class ApiUser(HttpUser):
    """Simulated shopper driving the five benchmark scenarios."""

    wait_time = between(1, 3)

    def on_start(self):
        """Create the per-user identity, session, customer, and cart."""
        self.user = self._load_user()
        self.auth_headers = {
            "Authorization": f"Bearer {RefreshToken.for_user(self.user).access_token}",
            "Cookie": _session_cookie(self.user),
            "Content-Type": "application/json",
        }
        self.customer = self._load_customer()
        self.billing_address = self._load_address(is_billing=True)
        self.shipping_address = self._load_address(is_shipping=True)
        self.cart_id = None
        self._create_cart()

    def _load_user(self):
        user_id = getattr(self, "_user_id", uuid.uuid4().hex)[:16]
        user, created = User.objects.get_or_create(
            email=f"locust-{user_id}@loadtest.local",
            defaults={
                "username": f"locust-{user_id}",
                "first_name": "Load",
                "last_name": "User",
            },
        )
        if created:
            user.set_password("loadtest-password")
            user.save()
        return user

    def _load_customer(self):
        customer = Customer.objects.filter(user=self.user).first()
        if customer is None:
            customer = Customer.objects.create(
                user=self.user, phone="555-0100", created_by=self.user
            )
        return customer

    def _load_address(self, *, is_billing=False, is_shipping=False):
        address = Address.objects.filter(
            user=self.user, is_billing=is_billing, is_shipping=is_shipping
        ).first()
        if address is None:
            address = Address.objects.create(
                user=self.user,
                address_line_1="1 Load Test Way",
                city="Springfield",
                state="IL",
                zip_code="62701",
                country="US",
                phone="555-0100",
                is_billing=is_billing,
                is_shipping=is_shipping,
                is_billing_default=is_billing,
                is_shipping_default=is_shipping,
                created_by=self.user,
            )
        return address

    def _create_cart(self):
        response = self.client.post(
            "/api/carts",
            json={"customer_id": str(self.customer.id)},
            headers=self.auth_headers,
            name="POST /api/carts",
        )
        if response.ok:
            self.cart_id = response.json()["id"]

    def _create_order(self):
        response = self.client.post(
            "/api/orders",
            json={
                "customer_id": str(self.customer.id),
                "billing_address_id": str(self.billing_address.id),
                "shipping_address_id": str(self.shipping_address.id),
                "email": self.user.email,
                "items": [
                    {
                        "product_variant_id": choice(VARIANT_IDS),
                        "quantity": randint(1, 2),
                    }
                ],
            },
            headers=self.auth_headers,
            name="POST /api/orders",
        )
        if response.ok:
            return response.json().get("id")
        return None

    @task(3)
    def list_products(self):
        """GET /api/products — Redis-cached for 300s."""
        self.client.get(
            "/api/products", headers=self.auth_headers, name="GET /api/products"
        )

    @task(2)
    def product_detail(self):
        """GET /api/products/{id} — Redis-cached for 600s."""
        product_id = choice(PRODUCT_IDS)
        self.client.get(
            f"/api/products/{product_id}",
            headers=self.auth_headers,
            name="GET /api/products/{id}",
        )

    @task(2)
    def add_cart_item(self):
        """POST /api/carts/{id}/items with a random variant."""
        if self.cart_id is None:
            return
        self.client.post(
            f"/api/carts/{self.cart_id}/items",
            json={
                "product_variant_id": choice(VARIANT_IDS),
                "quantity": randint(1, 3),
            },
            headers=self.auth_headers,
            name="POST /api/carts/{id}/items",
        )

    @task(2)
    def checkout(self):
        """POST /api/orders then POST /api/orders/{id}/submit."""
        order_id = self._create_order()
        if order_id is not None:
            self.client.post(
                f"/api/orders/{order_id}/submit",
                headers=self.auth_headers,
                name="POST /api/orders/{id}/submit",
            )

    @task(1)
    def create_order(self):
        """POST /api/orders with one line item."""
        self._create_order()
