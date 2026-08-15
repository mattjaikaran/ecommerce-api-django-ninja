"""Tests for LoyaltyService business logic."""

from decimal import Decimal

import pytest

from api.config.constants import LOYALTY_POINTS_PER_DOLLAR
from api.exceptions import ValidationError
from core.tests.factories import CustomerFactory
from loyalty.models import LoyaltyAccount, LoyaltyReason
from loyalty.services import LoyaltyService
from orders.tests.factories import OrderFactory

pytestmark = pytest.mark.django_db


class TestGetOrCreateAccount:
    def test_creates_account_lazily(self):
        customer = CustomerFactory()

        account = LoyaltyService.get_or_create_account(customer)

        assert account.customer == customer
        assert account.balance == Decimal("0.00")
        assert account.lifetime_points == Decimal("0.00")
        assert LoyaltyAccount.objects.count() == 1

    def test_returns_same_account_on_repeat_call(self):
        customer = CustomerFactory()

        first = LoyaltyService.get_or_create_account(customer)
        second = LoyaltyService.get_or_create_account(customer)

        assert first.id == second.id
        assert LoyaltyAccount.objects.count() == 1


class TestEarnPoints:
    def test_earn_credits_balance_and_lifetime_points(self):
        customer = CustomerFactory()
        order = OrderFactory(customer=customer, total=Decimal("100.00"))

        txn = LoyaltyService.earn_points(customer, order, order.total)

        expected = Decimal("100.00") * LOYALTY_POINTS_PER_DOLLAR
        assert txn.reason == LoyaltyReason.EARN
        assert txn.amount == expected
        assert txn.reference == f"order:{order.id}"
        assert txn.order == order
        account = LoyaltyService.get_account(customer)
        assert account.balance == expected
        assert account.lifetime_points == expected
        assert account.transactions.count() == 1

    def test_earn_floors_fractional_points(self):
        customer = CustomerFactory()
        order = OrderFactory(customer=customer, total=Decimal("10.99"))

        txn = LoyaltyService.earn_points(customer, order, order.total)

        assert txn.amount == Decimal(109)

    def test_earn_same_order_does_not_double_credit(self):
        customer = CustomerFactory()
        order = OrderFactory(customer=customer, total=Decimal("50.00"))

        first = LoyaltyService.earn_points(customer, order, order.total)
        second = LoyaltyService.earn_points(customer, order, order.total)

        account = LoyaltyService.get_account(customer)
        assert account.balance == Decimal(500)
        assert account.lifetime_points == Decimal(500)
        assert account.transactions.count() == 1
        assert second.id == first.id

    def test_earn_different_orders_credit_separately(self):
        customer = CustomerFactory()
        order1 = OrderFactory(customer=customer, total=Decimal("10.00"))
        order2 = OrderFactory(customer=customer, total=Decimal("20.00"))

        LoyaltyService.earn_points(customer, order1, order1.total)
        LoyaltyService.earn_points(customer, order2, order2.total)

        account = LoyaltyService.get_account(customer)
        assert account.balance == Decimal(300)
        assert account.transactions.count() == 2


class TestRedeemPoints:
    def test_redeem_debits_balance_and_records_negative_amount(self):
        customer = CustomerFactory()
        funding_order = OrderFactory(customer=customer, total=Decimal("100.00"))
        LoyaltyService.earn_points(customer, funding_order, funding_order.total)
        order = OrderFactory(customer=customer)

        txn = LoyaltyService.redeem_points(customer, Decimal(250), order)

        assert txn.reason == LoyaltyReason.REDEEM
        assert txn.amount == Decimal(-250)
        assert txn.reference == f"order:{order.id}"
        account = LoyaltyService.get_account(customer)
        assert account.balance == Decimal(750)

    def test_redeem_without_order_uses_empty_reference(self):
        customer = CustomerFactory()
        funding_order = OrderFactory(customer=customer, total=Decimal("10.00"))
        LoyaltyService.earn_points(customer, funding_order, funding_order.total)

        txn = LoyaltyService.redeem_points(customer, Decimal(100))

        assert txn.reference == ""
        assert txn.order is None

    def test_redeem_insufficient_balance_raises_validation_error(self):
        customer = CustomerFactory()
        funding_order = OrderFactory(customer=customer, total=Decimal("10.00"))
        LoyaltyService.earn_points(customer, funding_order, funding_order.total)

        with pytest.raises(ValidationError):
            LoyaltyService.redeem_points(customer, Decimal(500))

        account = LoyaltyService.get_account(customer)
        assert account.balance == Decimal(100)
        assert account.transactions.count() == 1

    def test_redeem_without_account_rejects_without_creating(self):
        customer = CustomerFactory()

        with pytest.raises(ValidationError):
            LoyaltyService.redeem_points(customer, Decimal(10))

        assert LoyaltyService.get_account(customer) is None
        assert LoyaltyService.get_balance(customer) == Decimal("0.00")


class TestGetBalance:
    def test_returns_balance_for_existing_account(self):
        customer = CustomerFactory()
        funding_order = OrderFactory(customer=customer, total=Decimal("50.00"))
        LoyaltyService.earn_points(customer, funding_order, funding_order.total)

        assert LoyaltyService.get_balance(customer) == Decimal(500)

    def test_returns_zero_without_account(self):
        customer = CustomerFactory()

        assert LoyaltyService.get_balance(customer) == Decimal("0.00")


class TestGetAccount:
    def test_returns_none_without_account(self):
        customer = CustomerFactory()

        assert LoyaltyService.get_account(customer) is None

    def test_returns_existing_account(self):
        customer = CustomerFactory()
        account = LoyaltyService.get_or_create_account(customer)

        assert LoyaltyService.get_account(customer).id == account.id
