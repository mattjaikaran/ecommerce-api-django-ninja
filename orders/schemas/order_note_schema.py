from datetime import datetime
from uuid import UUID

from ninja import Schema


class OrderNoteSchema(Schema):
    id: UUID
    order_id: UUID
    note: str
    is_internal: bool = False
    created_at: datetime


class OrderNoteCreateSchema(Schema):
    note: str
    is_internal: bool = False
