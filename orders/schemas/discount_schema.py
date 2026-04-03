from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ninja import Schema
from pydantic import Field


class DiscountSchema(Schema):
    id: UUID
    order_id: UUID
    amount: Decimal = Field(ge=0)
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class DiscountCreateSchema(Schema):
    order_id: UUID
    amount: Decimal = Field(ge=0)
    notes: str | None = None


class DiscountUpdateSchema(Schema):
    amount: Decimal | None = Field(ge=0, default=None)
    notes: str | None = None
