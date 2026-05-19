"""Business logic for payment processing via Stripe."""

import logging
from decimal import Decimal

import stripe
from django.conf import settings

from payments.models import PaymentMethod, PaymentRefund, PaymentTransaction
from payments.models.choices import PaymentGateway, PaymentStatus, RefundStatus

logger = logging.getLogger(__name__)


def _stripe():
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


class PaymentService:

    @staticmethod
    def attach_payment_method(user, stripe_payment_method_id: str, set_default: bool = False) -> PaymentMethod:
        """Retrieve card details from Stripe, create a local PaymentMethod record."""
        client = _stripe()
        pm_data = client.PaymentMethod.retrieve(stripe_payment_method_id)

        # Ensure customer has a Stripe customer record
        customer = user.customer
        if not customer.stripe_customer_id:
            stripe_customer = client.Customer.create(
                email=user.email,
                name=getattr(user, "full_name", None) or user.email,
            )
            customer.stripe_customer_id = stripe_customer["id"]
            customer.save(update_fields=["stripe_customer_id"])

        client.PaymentMethod.attach(stripe_payment_method_id, customer=customer.stripe_customer_id)

        if set_default:
            PaymentMethod.objects.filter(customer=customer).update(is_default=False)

        card = pm_data.get("card", {})
        pm = PaymentMethod.objects.create(
            customer=customer,
            stripe_payment_method_id=stripe_payment_method_id,
            stripe_customer_id=customer.stripe_customer_id,
            last_four=card.get("last4", ""),
            card_brand=card.get("brand", ""),
            expiry_month=card.get("exp_month"),
            expiry_year=card.get("exp_year"),
            is_default=set_default,
            created_by=user,
            updated_by=user,
        )
        return pm

    @staticmethod
    def create_payment_intent(order, payment_method: PaymentMethod, user) -> PaymentTransaction:
        """Create a Stripe PaymentIntent and record the transaction."""
        client = _stripe()

        # Order model uses 'total' field; support both 'total' and 'total_price'
        order_total = getattr(order, "total", None) or getattr(order, "total_price", 0)
        amount_cents = int(order_total * 100)
        intent = client.PaymentIntent.create(
            amount=amount_cents,
            currency=order.currency.lower() if hasattr(order, "currency") else "usd",
            customer=payment_method.stripe_customer_id,
            payment_method=payment_method.stripe_payment_method_id,
            confirm=True,
            metadata={"order_id": str(order.id), "order_number": order.order_number},
        )

        txn = PaymentTransaction.objects.create(
            order=order,
            payment_method=payment_method,
            gateway=PaymentGateway.STRIPE,
            status=PaymentStatus.PENDING,
            amount=order_total,
            currency=(order.currency.lower() if hasattr(order, "currency") else "USD").upper(),
            stripe_payment_intent_id=intent["id"],
            gateway_response=intent,
            created_by=user,
            updated_by=user,
        )
        return txn

    @staticmethod
    def create_refund(
        transaction: PaymentTransaction,
        amount: Decimal,
        reason: str,
        notes: str,
        user,
    ) -> PaymentRefund:
        """Issue a Stripe refund and record it locally."""
        client = _stripe()

        if not transaction.stripe_charge_id and not transaction.stripe_payment_intent_id:
            raise ValueError("Transaction has no Stripe charge or payment intent ID")

        kwargs: dict = {"amount": int(amount * 100), "reason": reason}
        if transaction.stripe_charge_id:
            kwargs["charge"] = transaction.stripe_charge_id
        else:
            kwargs["payment_intent"] = transaction.stripe_payment_intent_id

        stripe_refund = client.Refund.create(**kwargs)

        refund = PaymentRefund.objects.create(
            transaction=transaction,
            amount=amount,
            currency=transaction.currency,
            status=RefundStatus.PENDING,
            reason=reason,
            stripe_refund_id=stripe_refund["id"],
            gateway_response=stripe_refund,
            notes=notes,
            created_by=user,
            updated_by=user,
        )
        return refund

    @staticmethod
    def handle_payment_intent_succeeded(event_data: dict) -> None:
        intent = event_data["object"]
        PaymentTransaction.objects.filter(
            stripe_payment_intent_id=intent["id"]
        ).update(
            status=PaymentStatus.PAID,
            stripe_charge_id=intent.get("latest_charge", ""),
            gateway_response=intent,
        )
        logger.info("payment_intent.succeeded handled: %s", intent["id"])

    @staticmethod
    def handle_payment_intent_failed(event_data: dict) -> None:
        intent = event_data["object"]
        error = intent.get("last_payment_error") or {}
        PaymentTransaction.objects.filter(
            stripe_payment_intent_id=intent["id"]
        ).update(
            status=PaymentStatus.FAILED,
            error_code=error.get("code", ""),
            error_message=error.get("message", ""),
            gateway_response=intent,
        )
        logger.warning("payment_intent.payment_failed: %s", intent["id"])

    @staticmethod
    def handle_charge_refunded(event_data: dict) -> None:
        charge = event_data["object"]
        for stripe_refund in charge.get("refunds", {}).get("data", []):
            PaymentRefund.objects.filter(stripe_refund_id=stripe_refund["id"]).update(
                status=RefundStatus.SUCCEEDED,
                gateway_response=stripe_refund,
            )
        logger.info("charge.refunded handled: %s", charge["id"])
