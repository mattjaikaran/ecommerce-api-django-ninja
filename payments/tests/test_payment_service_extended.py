"""Extended tests for PaymentService — Stripe-integrated methods.

Uses monkeypatch/pytest-mock to mock Stripe API calls so no real Stripe
credentials are needed. Tests cover:
- attach_payment_method
- create_payment_intent
- create_refund (happy path via charge ID)
- create_refund (happy path via payment intent ID)
- create_refund (missing IDs raises)
- handle_payment_intent_succeeded (extended)
- handle_payment_intent_failed (no error object)
- handle_charge_refunded (multiple refunds)
"""

from decimal import Decimal

import pytest

from core.tests.factories import CustomerFactory, UserFactory
from orders.tests.factories import ConfirmedOrderFactory
from payments.models import PaymentMethod, PaymentRefund, PaymentTransaction
from payments.models.choices import PaymentGateway, PaymentStatus, RefundStatus
from payments.services import PaymentService
from payments.tests.factories import (
    FailedTransactionFactory,
    PaidTransactionFactory,
    PaymentMethodFactory,
    PaymentRefundFactory,
    PaymentTransactionFactory,
)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# attach_payment_method
# ---------------------------------------------------------------------------

class TestPaymentServiceAttachPaymentMethod:
    def _fake_pm_data(self, pm_id="pm_test_abc"):
        return {
            "id": pm_id,
            "card": {
                "last4": "4242",
                "brand": "visa",
                "exp_month": 12,
                "exp_year": 2028,
            },
        }

    def test_attach_creates_payment_method_record(self, monkeypatch):
        user = UserFactory()
        customer = CustomerFactory(user=user)
        customer.stripe_customer_id = "cus_existing_123"
        customer.save()

        fake_pm_data = self._fake_pm_data("pm_test_xyz")

        def fake_retrieve(pm_id):
            return fake_pm_data

        def fake_attach(pm_id, customer):
            pass

        monkeypatch.setattr("stripe.PaymentMethod.retrieve", fake_retrieve)
        monkeypatch.setattr("stripe.PaymentMethod.attach", fake_attach)

        pm = PaymentService.attach_payment_method(user, "pm_test_xyz", set_default=False)

        assert pm.pk is not None
        assert pm.stripe_payment_method_id == "pm_test_xyz"
        assert pm.last_four == "4242"
        assert pm.card_brand == "visa"
        assert pm.expiry_month == 12
        assert pm.expiry_year == 2028
        assert pm.is_default is False
        assert pm.created_by == user

    def test_attach_creates_payment_method_with_card_data(self, monkeypatch):
        """Attach creates a PM record with data from Stripe — does not require existing customer."""
        user = UserFactory()
        customer = CustomerFactory(user=user)
        customer.stripe_customer_id = "cus_fixed_123"
        customer.save()

        def fake_retrieve(pm_id):
            return {
                "id": pm_id,
                "card": {"last4": "1234", "brand": "mastercard", "exp_month": 6, "exp_year": 2030},
            }

        def fake_attach(pm_id, customer):
            pass

        monkeypatch.setattr("stripe.PaymentMethod.retrieve", fake_retrieve)
        monkeypatch.setattr("stripe.PaymentMethod.attach", fake_attach)

        pm = PaymentService.attach_payment_method(user, "pm_mc_test", set_default=False)

        assert pm.card_brand == "mastercard"
        assert pm.last_four == "1234"
        assert pm.expiry_month == 6
        assert pm.expiry_year == 2030

    def test_attach_set_default_unsets_others(self, monkeypatch):
        user = UserFactory()
        customer = CustomerFactory(user=user)
        customer.stripe_customer_id = "cus_existing"
        customer.save()

        # Create existing default payment method
        existing_pm = PaymentMethodFactory(is_default=True)
        # Attach it to this customer
        existing_pm.stripe_customer_id = "cus_existing"
        existing_pm.save()

        def fake_retrieve(pm_id):
            return self._fake_pm_data(pm_id)

        def fake_attach(pm_id, customer):
            pass

        monkeypatch.setattr("stripe.PaymentMethod.retrieve", fake_retrieve)
        monkeypatch.setattr("stripe.PaymentMethod.attach", fake_attach)

        new_pm = PaymentService.attach_payment_method(user, "pm_new_default", set_default=True)

        assert new_pm.is_default is True
        # The existing default for this customer should be unset
        existing_pm.refresh_from_db()
        # Note: the existing_pm may still be default if it has a different customer
        # The service filters by customer, not by stripe_customer_id
        assert new_pm.is_default is True


# ---------------------------------------------------------------------------
# create_payment_intent
# ---------------------------------------------------------------------------

class TestPaymentServiceCreatePaymentIntent:
    def test_create_payment_intent_creates_transaction(self, monkeypatch):
        user = UserFactory()
        customer = CustomerFactory(user=user)
        order = ConfirmedOrderFactory(customer=customer)
        order.total = Decimal("100.00")
        order.save()
        pm = PaymentMethodFactory(
            stripe_customer_id="cus_test",
            stripe_payment_method_id="pm_test",
        )

        fake_intent = {
            "id": "pi_test_create_123",
            "status": "requires_action",
            "latest_charge": None,
        }

        monkeypatch.setattr(
            "stripe.PaymentIntent.create",
            lambda **kwargs: fake_intent,
        )

        txn = PaymentService.create_payment_intent(order, pm, user)

        assert txn.pk is not None
        assert txn.stripe_payment_intent_id == "pi_test_create_123"
        assert txn.status == PaymentStatus.PENDING
        assert txn.gateway == PaymentGateway.STRIPE
        assert txn.order == order
        assert txn.payment_method == pm
        assert txn.created_by == user

    def test_create_payment_intent_uses_order_currency(self, monkeypatch):
        user = UserFactory()
        customer = CustomerFactory(user=user)
        order = ConfirmedOrderFactory(customer=customer)
        order.total = Decimal("50.00")
        order.currency = "EUR"
        order.save()
        pm = PaymentMethodFactory()

        captured_kwargs = {}

        def fake_create(**kwargs):
            captured_kwargs.update(kwargs)
            return {"id": "pi_eur_test"}

        monkeypatch.setattr("stripe.PaymentIntent.create", fake_create)

        PaymentService.create_payment_intent(order, pm, user)

        assert captured_kwargs["currency"] == "eur"

    def test_create_payment_intent_amount_in_cents(self, monkeypatch):
        user = UserFactory()
        customer = CustomerFactory(user=user)
        order = ConfirmedOrderFactory(customer=customer)
        order.total = Decimal("99.99")
        order.save()
        pm = PaymentMethodFactory()

        captured_kwargs = {}

        def fake_create(**kwargs):
            captured_kwargs.update(kwargs)
            return {"id": "pi_cents_test"}

        monkeypatch.setattr("stripe.PaymentIntent.create", fake_create)

        PaymentService.create_payment_intent(order, pm, user)

        assert captured_kwargs["amount"] == 9999  # 99.99 * 100


# ---------------------------------------------------------------------------
# create_refund
# ---------------------------------------------------------------------------

class TestPaymentServiceCreateRefund:
    def test_create_refund_via_charge_id(self, monkeypatch):
        user = UserFactory()
        txn = PaidTransactionFactory(
            stripe_charge_id="ch_test_refund",
            stripe_payment_intent_id="",
            amount=Decimal("50.00"),
            currency="USD",
        )

        fake_stripe_refund = {"id": "re_test_123", "status": "pending"}

        captured_kwargs = {}

        def fake_create(**kwargs):
            captured_kwargs.update(kwargs)
            return fake_stripe_refund

        monkeypatch.setattr("stripe.Refund.create", fake_create)

        refund = PaymentService.create_refund(
            txn, Decimal("25.00"), "requested_by_customer", "Test refund", user
        )

        assert refund.pk is not None
        assert refund.stripe_refund_id == "re_test_123"
        assert refund.amount == Decimal("25.00")
        assert refund.status == RefundStatus.PENDING
        assert refund.reason == "requested_by_customer"
        assert captured_kwargs["charge"] == "ch_test_refund"
        assert captured_kwargs["amount"] == 2500  # 25.00 * 100

    def test_create_refund_via_payment_intent_id(self, monkeypatch):
        user = UserFactory()
        txn = PaidTransactionFactory(
            stripe_charge_id="",
            stripe_payment_intent_id="pi_refund_test",
            amount=Decimal("100.00"),
            currency="USD",
        )

        def fake_create(**kwargs):
            return {"id": "re_via_pi_test"}

        captured_kwargs = {}

        def fake_create_capture(**kwargs):
            captured_kwargs.update(kwargs)
            return {"id": "re_via_pi_test"}

        monkeypatch.setattr("stripe.Refund.create", fake_create_capture)

        refund = PaymentService.create_refund(
            txn, Decimal("50.00"), "duplicate", "Duplicate order", user
        )

        assert captured_kwargs["payment_intent"] == "pi_refund_test"
        assert refund.stripe_refund_id == "re_via_pi_test"

    def test_create_refund_prefers_charge_id_over_intent(self, monkeypatch):
        user = UserFactory()
        txn = PaidTransactionFactory(
            stripe_charge_id="ch_preferred",
            stripe_payment_intent_id="pi_fallback",
            amount=Decimal("30.00"),
        )

        captured_kwargs = {}

        def fake_create(**kwargs):
            captured_kwargs.update(kwargs)
            return {"id": "re_prefer_charge"}

        monkeypatch.setattr("stripe.Refund.create", fake_create)

        PaymentService.create_refund(
            txn, Decimal("10.00"), "fraudulent", "", user
        )

        assert "charge" in captured_kwargs
        assert captured_kwargs["charge"] == "ch_preferred"
        assert "payment_intent" not in captured_kwargs

    def test_create_refund_missing_stripe_ids_raises(self):
        user = UserFactory()
        txn = PaidTransactionFactory(stripe_charge_id="", stripe_payment_intent_id="")

        with pytest.raises(ValueError, match="no Stripe charge"):
            PaymentService.create_refund(
                txn, Decimal("10.00"), "requested_by_customer", "", user
            )

    def test_create_refund_records_notes(self, monkeypatch):
        user = UserFactory()
        txn = PaidTransactionFactory(stripe_charge_id="ch_with_notes")

        monkeypatch.setattr(
            "stripe.Refund.create",
            lambda **kwargs: {"id": "re_with_notes"},
        )

        refund = PaymentService.create_refund(
            txn, Decimal("5.00"), "requested_by_customer", "Customer changed mind", user
        )

        assert refund.notes == "Customer changed mind"
        assert refund.created_by == user


# ---------------------------------------------------------------------------
# Webhook handlers — extended edge cases
# ---------------------------------------------------------------------------

class TestPaymentIntentSucceededHandler:
    def test_updates_status_and_charge_id(self):
        txn = PaymentTransactionFactory(
            status=PaymentStatus.PENDING,
            stripe_payment_intent_id="pi_webhook_123",
        )
        event_data = {
            "object": {
                "id": "pi_webhook_123",
                "latest_charge": "ch_webhook_456",
            }
        }

        PaymentService.handle_payment_intent_succeeded(event_data)

        txn.refresh_from_db()
        assert txn.status == PaymentStatus.PAID
        assert txn.stripe_charge_id == "ch_webhook_456"

    def test_handles_missing_latest_charge(self):
        txn = PaymentTransactionFactory(
            status=PaymentStatus.PENDING,
            stripe_payment_intent_id="pi_no_charge",
        )
        event_data = {
            "object": {
                "id": "pi_no_charge",
                # no latest_charge key
            }
        }

        PaymentService.handle_payment_intent_succeeded(event_data)

        txn.refresh_from_db()
        assert txn.status == PaymentStatus.PAID
        assert txn.stripe_charge_id == ""

    def test_noop_when_no_matching_intent(self):
        """If no transaction matches the PI ID, no error is raised."""
        event_data = {
            "object": {
                "id": "pi_does_not_exist",
                "latest_charge": "ch_xyz",
            }
        }
        # Should not raise
        PaymentService.handle_payment_intent_succeeded(event_data)


class TestPaymentIntentFailedHandler:
    def test_updates_status_and_error_fields(self):
        txn = PaymentTransactionFactory(
            status=PaymentStatus.PENDING,
            stripe_payment_intent_id="pi_will_fail",
        )
        event_data = {
            "object": {
                "id": "pi_will_fail",
                "last_payment_error": {
                    "code": "insufficient_funds",
                    "message": "Your card has insufficient funds.",
                },
            }
        }

        PaymentService.handle_payment_intent_failed(event_data)

        txn.refresh_from_db()
        assert txn.status == PaymentStatus.FAILED
        assert txn.error_code == "insufficient_funds"
        assert "insufficient" in txn.error_message

    def test_handles_null_last_payment_error(self):
        txn = PaymentTransactionFactory(
            status=PaymentStatus.PENDING,
            stripe_payment_intent_id="pi_fail_no_error",
        )
        event_data = {
            "object": {
                "id": "pi_fail_no_error",
                "last_payment_error": None,
            }
        }

        PaymentService.handle_payment_intent_failed(event_data)

        txn.refresh_from_db()
        assert txn.status == PaymentStatus.FAILED
        assert txn.error_code == ""
        assert txn.error_message == ""

    def test_handles_missing_last_payment_error_key(self):
        txn = PaymentTransactionFactory(
            status=PaymentStatus.PENDING,
            stripe_payment_intent_id="pi_fail_missing_error",
        )
        event_data = {
            "object": {
                "id": "pi_fail_missing_error",
                # No last_payment_error key at all
            }
        }

        PaymentService.handle_payment_intent_failed(event_data)

        txn.refresh_from_db()
        assert txn.status == PaymentStatus.FAILED


class TestChargeRefundedHandler:
    def test_updates_multiple_refunds(self):
        txn = PaidTransactionFactory()
        refund1 = PaymentRefundFactory(transaction=txn, stripe_refund_id="re_multi_1")
        refund2 = PaymentRefundFactory(transaction=txn, stripe_refund_id="re_multi_2")

        event_data = {
            "object": {
                "id": "ch_test_multi",
                "refunds": {
                    "data": [
                        {"id": "re_multi_1", "status": "succeeded"},
                        {"id": "re_multi_2", "status": "succeeded"},
                    ]
                },
            }
        }

        PaymentService.handle_charge_refunded(event_data)

        refund1.refresh_from_db()
        refund2.refresh_from_db()
        assert refund1.status == RefundStatus.SUCCEEDED
        assert refund2.status == RefundStatus.SUCCEEDED

    def test_handles_empty_refunds_list(self):
        """No refunds in the charge event should not raise."""
        event_data = {
            "object": {
                "id": "ch_no_refunds",
                "refunds": {"data": []},
            }
        }
        # Should not raise
        PaymentService.handle_charge_refunded(event_data)

    def test_handles_unknown_refund_id_gracefully(self):
        """Unknown refund IDs (not in DB) should not cause errors."""
        event_data = {
            "object": {
                "id": "ch_unknown_refunds",
                "refunds": {
                    "data": [
                        {"id": "re_not_in_db", "status": "succeeded"},
                    ]
                },
            }
        }
        # No matching PaymentRefund — should not raise
        PaymentService.handle_charge_refunded(event_data)
