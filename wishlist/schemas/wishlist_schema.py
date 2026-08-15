from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ninja import Schema
from pydantic import Field


class WishlistProductVariantSchema(Schema):
    id: UUID
    name: str
    sku: str
    price: Decimal


class WishlistItemCreateSchema(Schema):
    product_variant_id: UUID
    quantity: int = Field(default=1, ge=1)
    notes: str | None = None


class WishlistItemSchema(Schema):
    id: UUID
    product_variant_id: UUID
    product_variant: WishlistProductVariantSchema
    quantity: int
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    message: str | None = None


class WishlistSchema(Schema):
    id: UUID
    customer_id: UUID
    name: str | None = None
    items: list[WishlistItemSchema]
    created_at: datetime
    updated_at: datetime


class WishlistExistsResponseSchema(Schema):
    exists: bool
