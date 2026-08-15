from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ninja import Schema
from pydantic import Field


class LoyaltyAccountSchema(Schema):
    id: UUID
    customer_id: UUID
    balance: Decimal
    lifetime_points: Decimal
    created_at: datetime
    updated_at: datetime


class LoyaltyTransactionSchema(Schema):
    id: UUID
    account_id: UUID
    amount: Decimal
    reason: str
    order_id: UUID | None = None
    reference: str
    created_at: datetime


class LoyaltyRedeemSchema(Schema):
    points: int = Field(gt=0)
    order_id: UUID | None = None
