"""Tests for PaymentService business logic."""


import pytest

from payments.models.choices import PaymentStatus, RefundStatus
from payments.services import PaymentService
from payments.tests.factories import PaidTransactionFactory

pytestmark = pytest.mark.django_db


class TestPaymentServiceHandlers:
    def test_handle_payment_intent_succeeded(self, db):
        txn = PaidTransactionFactory(
            status=PaymentStatus.PENDING,
            stripe_payment_intent_id="pi_test_123",
        )
        event_data = {
            "object": {
                "id": "pi_test_123",
                "latest_charge": "ch_test_456",
            }
        }
        PaymentService.handle_payment_intent_succeeded(event_data)
        txn.refresh_from_db()
        assert txn.status == PaymentStatus.PAID
        assert txn.stripe_charge_id == "ch_test_456"

    def test_handle_payment_intent_failed(self, db):
        txn = PaidTransactionFactory(
            status=PaymentStatus.PENDING,
            stripe_payment_intent_id="pi_fail_test",
        )
        event_data = {
            "object": {
                "id": "pi_fail_test",
                "last_payment_error": {
                    "code": "card_declined",
                    "message": "Your card was declined.",
                },
            }
        }
        PaymentService.handle_payment_intent_failed(event_data)
        txn.refresh_from_db()
        assert txn.status == PaymentStatus.FAILED
        assert txn.error_code == "card_declined"
        assert "declined" in txn.error_message

    def test_handle_charge_refunded(self, db):
        from payments.tests.factories import PaymentRefundFactory
        refund = PaymentRefundFactory(stripe_refund_id="re_test_789")

        event_data = {
            "object": {
                "id": "ch_test",
                "refunds": {
                    "data": [
                        {"id": "re_test_789", "status": "succeeded"}
                    ]
                },
            }
        }
        PaymentService.handle_charge_refunded(event_data)
        refund.refresh_from_db()
        assert refund.status == RefundStatus.SUCCEEDED

    def test_create_refund_requires_stripe_id(self, db):
        from decimal import Decimal

        from core.tests.factories import UserFactory
        txn = PaidTransactionFactory(stripe_charge_id="", stripe_payment_intent_id="")
        user = UserFactory()
        with pytest.raises(ValueError, match="no Stripe charge"):
            PaymentService.create_refund(txn, Decimal("10.00"), "requested_by_customer", "", user)
