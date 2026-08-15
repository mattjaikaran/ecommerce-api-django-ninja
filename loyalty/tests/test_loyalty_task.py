"""Tests for the credit_order_points Celery task."""

from decimal import Decimal

import pytest

from core.tests.factories import CustomerFactory
from loyalty.services import LoyaltyService
from loyalty.tasks import credit_order_points
from orders.tests.factories import OrderFactory

pytestmark = pytest.mark.django_db


class TestCreditOrderPointsTask:
    def test_credits_account_once(self):
        customer = CustomerFactory()
        order = OrderFactory(customer=customer, total=Decimal("25.00"))

        credit_order_points(order.id)

        account = LoyaltyService.get_account(customer)
        assert account is not None
        assert account.balance == Decimal(250)
        assert account.lifetime_points == Decimal(250)
        assert account.transactions.count() == 1

    def test_no_double_credit_on_replay(self):
        customer = CustomerFactory()
        order = OrderFactory(customer=customer, total=Decimal("25.00"))

        credit_order_points(order.id)
        credit_order_points(order.id)

        account = LoyaltyService.get_account(customer)
        assert account.balance == Decimal(250)
        assert account.lifetime_points == Decimal(250)
        assert account.transactions.count() == 1
