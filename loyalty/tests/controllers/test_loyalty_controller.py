"""Tests for LoyaltyController HTTP endpoints."""

from decimal import Decimal

import pytest
from django.test import Client

from core.tests.factories import CustomerFactory, UserFactory
from loyalty.models import LoyaltyAccount, LoyaltyReason
from loyalty.tests.factories import LoyaltyAccountFactory, LoyaltyTransactionFactory
from orders.tests.factories import OrderFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def customer(user):
    return CustomerFactory(user=user)


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client, user


class TestBalanceEndpoint:
    def test_balance_requires_auth(self, client):
        response = client.get("/api/loyalty/balance")

        assert response.status_code in (401, 403)

    def test_balance_returns_account(self, auth_client, customer):
        c, _ = auth_client
        account = LoyaltyAccountFactory(
            customer=customer,
            balance=Decimal("150.00"),
            lifetime_points=Decimal("200.00"),
        )

        response = c.get("/api/loyalty/balance")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(account.id)
        assert data["customer_id"] == str(customer.id)
        assert data["balance"] == "150.00"
        assert data["lifetime_points"] == "200.00"

    def test_balance_without_account_returns_404(self, auth_client):
        c, _ = auth_client

        response = c.get("/api/loyalty/balance")

        assert response.status_code == 404

    def test_cannot_see_another_users_account(self, auth_client):
        c, _ = auth_client
        other = CustomerFactory()
        LoyaltyAccountFactory(customer=other, balance=Decimal("999.00"))

        response = c.get("/api/loyalty/balance")

        assert response.status_code == 404


class TestTransactionsEndpoint:
    def test_transactions_requires_auth(self, client):
        response = client.get("/api/loyalty/transactions")

        assert response.status_code in (401, 403)

    def test_transactions_paginated_own_only(self, auth_client, customer):
        c, _ = auth_client
        account = LoyaltyAccountFactory(customer=customer)
        own = LoyaltyTransactionFactory.create_batch(
            3, account=account, reason=LoyaltyReason.EARN
        )
        other_account = LoyaltyAccountFactory()
        LoyaltyTransactionFactory.create_batch(
            2, account=other_account, reason=LoyaltyReason.EARN
        )

        response = c.get("/api/loyalty/transactions")

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["count"] == 3
        result_ids = {item["id"] for item in data["results"]}
        assert result_ids == {str(txn.id) for txn in own}

    def test_transactions_without_account_returns_404(self, auth_client):
        c, _ = auth_client

        response = c.get("/api/loyalty/transactions")

        assert response.status_code == 404


class TestRedeemEndpoint:
    def test_redeem_requires_auth(self, client):
        response = client.post(
            "/api/loyalty/redeem",
            data={"points": 100},
            content_type="application/json",
        )

        assert response.status_code in (401, 403)

    def test_redeem_creates_debit_transaction(self, auth_client, customer):
        c, _ = auth_client
        account = LoyaltyAccountFactory(
            customer=customer,
            balance=Decimal("500.00"),
            lifetime_points=Decimal("1000.00"),
        )
        order = OrderFactory(customer=customer)

        response = c.post(
            "/api/loyalty/redeem",
            data={"points": 100, "order_id": str(order.id)},
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["reason"] == LoyaltyReason.REDEEM
        assert data["amount"] == "-100"
        assert data["order_id"] == str(order.id)
        account.refresh_from_db()
        assert account.balance == Decimal("400.00")

    def test_redeem_insufficient_balance_returns_400(self, auth_client, customer):
        c, _ = auth_client
        LoyaltyAccountFactory(customer=customer, balance=Decimal("50.00"))

        response = c.post(
            "/api/loyalty/redeem",
            data={"points": 100},
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_redeem_without_account_returns_400(self, auth_client, customer):
        c, _ = auth_client

        response = c.post(
            "/api/loyalty/redeem",
            data={"points": 10},
            content_type="application/json",
        )

        assert response.status_code == 400
        assert not LoyaltyAccount.objects.filter(customer=customer).exists()

    def test_redeem_foreign_order_returns_404(self, auth_client, customer):
        c, _ = auth_client
        LoyaltyAccountFactory(customer=customer, balance=Decimal("500.00"))
        other = CustomerFactory()
        foreign_order = OrderFactory(customer=other)

        response = c.post(
            "/api/loyalty/redeem",
            data={"points": 10, "order_id": str(foreign_order.id)},
            content_type="application/json",
        )

        assert response.status_code == 404
