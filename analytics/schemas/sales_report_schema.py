from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ninja import Schema
from pydantic import Field


class SalesReportSchema(Schema):
    id: UUID
    report_type: str
    period: str
    period_start: datetime
    period_end: datetime
    total_revenue: Decimal = Field(ge=0)
    total_orders: int
    total_items_sold: int
    average_order_value: Decimal = Field(ge=0)
    total_discounts: Decimal = Field(ge=0)
    total_refunds: Decimal = Field(ge=0)
    total_tax: Decimal = Field(ge=0)
    total_shipping: Decimal = Field(ge=0)
    net_revenue: Decimal
    new_customers: int
    returning_customers: int
    meta_data: dict = {}
    created_at: datetime
    updated_at: datetime


class SalesReportFilterSchema(Schema):
    report_type: str | None = None
    period: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
