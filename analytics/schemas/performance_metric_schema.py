from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ninja import Schema


class PerformanceMetricSchema(Schema):
    id: UUID
    metric_type: str
    period: str
    period_start: datetime
    period_end: datetime
    value: Decimal
    previous_value: Decimal | None = None
    change_percentage: Decimal | None = None
    meta_data: dict = {}
    created_at: datetime
    updated_at: datetime
