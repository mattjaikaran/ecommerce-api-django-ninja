"""Pydantic schemas for the payments app."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ninja import Schema


class PaymentMethodSchema(Schema):
    id: UUID
    type: str
    provider: str
    is_default: bool
    last_four: str
    card_brand: str
    expiry_month: int | None
    expiry_year: int | None
    stripe_payment_method_id: str
    is_active: bool
    created_at: datetime


class PaymentMethodCreateSchema(Schema):
    stripe_payment_method_id: str
    is_default: bool = False


class PaymentTransactionSchema(Schema):
    id: UUID
    order_id: UUID
    payment_method_id: UUID | None
    gateway: str
    status: str
    amount: Decimal
    currency: str
    fee: Decimal
    stripe_payment_intent_id: str
    stripe_charge_id: str
    error_code: str
    error_message: str
    created_at: datetime


class PaymentRefundSchema(Schema):
    id: UUID
    transaction_id: UUID
    amount: Decimal
    currency: str
    status: str
    reason: str
    stripe_refund_id: str
    notes: str
    created_at: datetime


class PaymentRefundCreateSchema(Schema):
    amount: Decimal
    reason: str = "requested_by_customer"
    notes: str = ""


class StripeWebhookEventSchema(Schema):
    id: UUID
    stripe_event_id: str
    event_type: str
    status: str
    received_at: datetime
    processed_at: datetime | None
    error: str
