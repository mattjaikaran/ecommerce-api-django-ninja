from datetime import datetime
from uuid import UUID

from ninja import Schema


class OrderHistorySchema(Schema):
    id: UUID
    order_id: UUID
    status: str
    notes: str = ""
    created_at: datetime
    updated_at: datetime


class OrderHistoryCreateSchema(Schema):
    order_id: UUID
    status: str
    notes: str = ""
