from datetime import datetime
from uuid import UUID

from ninja import Schema

from .user_schema import UserSchema


class CustomerSchema(Schema):
    id: UUID
    user: UserSchema
    phone: str | None = None
    customer_group_id: UUID | None = None
    meta_data: dict = {}
    is_default: bool = False
    is_active: bool = True
    is_deleted: bool = False
    deleted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CustomerCreateSchema(Schema):
    user_id: UUID
    phone: str | None = None
    customer_group_id: UUID | None = None
    meta_data: dict = {}
    is_default: bool = False


class CustomerUpdateSchema(Schema):
    phone: str | None = None
    customer_group_id: UUID | None = None
    meta_data: dict | None = None
    is_default: bool | None = None
