from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ninja import Schema
from pydantic import Field, validator

from coupons.models.choices import DiscountType


class CouponSchema(Schema):
    id: UUID
    code: str
    description: str | None = None
    discount_type: str
    discount_value: Decimal = Field(ge=0)
    max_discount_amount: Decimal | None = None
    min_order_amount: Decimal = Field(ge=0)
    usage_limit: int | None = None
    usage_limit_per_customer: int | None = None
    used_count: int
    valid_from: datetime
    valid_to: datetime
    is_active: bool
    customer_group_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class CouponCreateSchema(Schema):
    code: str = Field(min_length=1, max_length=50)
    description: str | None = None
    discount_type: DiscountType
    discount_value: Decimal = Field(ge=0)
    max_discount_amount: Decimal | None = Field(default=None, ge=0)
    min_order_amount: Decimal = Field(default=Decimal("0"), ge=0)
    usage_limit: int | None = Field(default=None, ge=1)
    usage_limit_per_customer: int | None = Field(default=None, ge=1)
    valid_from: datetime
    valid_to: datetime
    is_active: bool = True
    customer_group_id: UUID | None = None
    restricted_customer_ids: list[UUID] | None = None

    @validator("discount_value")
    def validate_discount_value(cls, v, values):
        if values.get("discount_type") == DiscountType.PERCENTAGE and v > 100:
            raise ValueError("Percentage discount cannot exceed 100")
        return v

    @validator("valid_to")
    def validate_dates(cls, v, values):
        if "valid_from" in values and v <= values["valid_from"]:
            raise ValueError("valid_to must be after valid_from")
        return v


class CouponUpdateSchema(Schema):
    description: str | None = None
    discount_type: DiscountType | None = None
    discount_value: Decimal | None = Field(default=None, ge=0)
    max_discount_amount: Decimal | None = Field(default=None, ge=0)
    min_order_amount: Decimal | None = Field(default=None, ge=0)
    usage_limit: int | None = Field(default=None, ge=1)
    usage_limit_per_customer: int | None = Field(default=None, ge=1)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    is_active: bool | None = None
    customer_group_id: UUID | None = None
    restricted_customer_ids: list[UUID] | None = None


class ApplyCouponSchema(Schema):
    code: str
    order_id: UUID


class CouponValidateSchema(Schema):
    code: str
    order_subtotal: Decimal = Field(ge=0)


class CouponValidateResponseSchema(Schema):
    valid: bool
    discount_amount: Decimal
    shipping_discount: Decimal
    message: str


class CouponUsageSchema(Schema):
    id: UUID
    coupon_id: UUID
    coupon_code: str
    customer_id: UUID
    order_id: UUID | None = None
    discount_applied: Decimal
    created_at: datetime
