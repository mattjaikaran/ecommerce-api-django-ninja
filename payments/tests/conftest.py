"""Shared fixtures for payments tests."""

import pytest

from .factories import (
    PaidTransactionFactory,
    PaymentMethodFactory,
    PaymentTransactionFactory,
)


@pytest.fixture
def payment_method(db):
    return PaymentMethodFactory()


@pytest.fixture
def payment_transaction(db):
    return PaymentTransactionFactory()


@pytest.fixture
def paid_transaction(db):
    return PaidTransactionFactory()
