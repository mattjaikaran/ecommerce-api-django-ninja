from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ninja import Schema


class CustomerAnalyticsSchema(Schema):
    id: UUID
    customer_id: UUID
    period: str
    period_start: datetime
    period_end: datetime
    total_orders: int
    total_spent: Decimal
    average_order_value: Decimal
    total_returns: int
    lifetime_value: Decimal
    meta_data: dict = {}
    created_at: datetime
    updated_at: datetime
