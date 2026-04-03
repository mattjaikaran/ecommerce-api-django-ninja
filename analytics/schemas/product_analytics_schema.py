from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ninja import Schema


class ProductAnalyticsSchema(Schema):
    id: UUID
    product_id: UUID
    period: str
    period_start: datetime
    period_end: datetime
    units_sold: int
    revenue: Decimal
    views: int
    conversion_rate: Decimal
    returns: int
    average_rating: Decimal | None = None
    meta_data: dict = {}
    created_at: datetime
    updated_at: datetime
