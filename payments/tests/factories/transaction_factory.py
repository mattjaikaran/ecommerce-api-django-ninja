"""Factories for PaymentTransaction and PaymentRefund models."""

from decimal import Decimal

import factory

from orders.tests.factories import OrderFactory
from payments.models import PaymentRefund, PaymentTransaction
from payments.models.choices import PaymentGateway, PaymentStatus

from .payment_method_factory import PaymentMethodFactory


class PaymentTransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PaymentTransaction

    order = factory.SubFactory(OrderFactory)
    payment_method = factory.SubFactory(PaymentMethodFactory)
    gateway = PaymentGateway.STRIPE
    status = PaymentStatus.PENDING
    amount = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True, min_value=Decimal("1.00"))
    currency = "USD"
    fee = Decimal("0.00")
    stripe_payment_intent_id = factory.Sequence(lambda n: f"pi_test_{n:06d}")
    gateway_response = factory.LazyFunction(dict)
    created_by = factory.SelfAttribute("order.customer.user")
    updated_by = factory.SelfAttribute("order.customer.user")


class PaidTransactionFactory(PaymentTransactionFactory):
    status = PaymentStatus.PAID
    stripe_charge_id = factory.Sequence(lambda n: f"ch_test_{n:06d}")


class FailedTransactionFactory(PaymentTransactionFactory):
    status = PaymentStatus.FAILED
    error_code = "card_declined"
    error_message = "Your card was declined."


class PaymentRefundFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PaymentRefund

    transaction = factory.SubFactory(PaidTransactionFactory)
    amount = factory.LazyAttribute(lambda obj: obj.transaction.amount)
    currency = "USD"
    status = "pending"
    reason = "requested_by_customer"
    stripe_refund_id = factory.Sequence(lambda n: f"re_test_{n:06d}")
    gateway_response = factory.LazyFunction(dict)
    created_by = factory.SelfAttribute("transaction.created_by")
    updated_by = factory.SelfAttribute("transaction.created_by")
