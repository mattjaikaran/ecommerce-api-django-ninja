from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ninja import Schema
from pydantic import Field, validator

from orders.models import OrderStatus, PaymentMethod, PaymentStatus, ShippingMethod

from .fulfillment_schema import FulfillmentOrderSchema
from .order_line_item_schema import OrderLineItemSchema
from .payment_schema import PaymentTransactionSchema
from .refund_schema import RefundSchema
from .tax_schema import TaxSchema


class OrderSchema(Schema):
    id: UUID
    order_number: str
    customer_id: UUID
    customer_group_id: UUID | None = None
    status: str = OrderStatus.DRAFT
    currency: str = "USD"
    subtotal: Decimal = Field(ge=0)
    shipping_amount: Decimal = Field(ge=0)
    shipping_method: str = ShippingMethod.STANDARD
    shipping_tax_amount: Decimal = Field(ge=0)
    discount_amount: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(ge=0)
    total: Decimal = Field(ge=0)
    payment_status: str = PaymentStatus.PENDING
    payment_method: str = PaymentMethod.CREDIT_CARD
    payment_gateway: str | None = None
    payment_gateway_id: str | None = None
    payment_gateway_response: dict | None = None
    billing_address_id: UUID
    shipping_address_id: UUID
    email: str
    phone: str | None = None
    customer_note: str | None = None
    staff_notes: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    meta_data: dict = {}
    items: list[OrderLineItemSchema]
    fulfillments: list[FulfillmentOrderSchema]
    transactions: list[PaymentTransactionSchema]
    refunds: list[RefundSchema]
    taxes: list[TaxSchema]
    notes: list[dict]
    history: list[dict]
    created_at: datetime
    updated_at: datetime

    @validator("total")
    def validate_total(cls, v, values):
        if "subtotal" in values and v < values["subtotal"]:
            raise ValueError("Total cannot be less than subtotal")
        return v


class OrderCreateSchema(Schema):
    customer_id: UUID
    customer_group_id: UUID | None = None
    currency: str = "USD"
    shipping_method: str = ShippingMethod.STANDARD
    payment_method: str = PaymentMethod.CREDIT_CARD
    payment_gateway: str | None = None
    billing_address_id: UUID
    shipping_address_id: UUID
    email: str
    phone: str | None = None
    customer_note: str | None = None
    meta_data: dict = {}
    items: list[dict]  # List of {product_variant_id: UUID, quantity: int}


class OrderUpdateSchema(Schema):
    status: str | None = None
    shipping_method: str | None = None
    payment_method: str | None = None
    payment_gateway: str | None = None
    billing_address_id: UUID | None = None
    shipping_address_id: UUID | None = None
    email: str | None = None
    phone: str | None = None
    customer_note: str | None = None
    staff_notes: str | None = None
    meta_data: dict | None = None
