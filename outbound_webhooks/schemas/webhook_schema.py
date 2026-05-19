from datetime import datetime
from uuid import UUID

from ninja import Schema


class WebhookEndpointSchema(Schema):
    id: UUID
    url: str
    description: str | None = None
    events: list[str]
    is_active: bool
    failure_count: int
    last_success_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class WebhookEndpointCreateSchema(Schema):
    url: str
    description: str | None = None
    events: list[str]
    is_active: bool = True


class WebhookEndpointUpdateSchema(Schema):
    url: str | None = None
    description: str | None = None
    events: list[str] | None = None
    is_active: bool | None = None


class WebhookDeliverySchema(Schema):
    id: UUID
    endpoint_id: UUID
    event_type: str
    payload: dict
    status: str
    response_status_code: int | None = None
    response_body: str | None = None
    attempt_count: int
    delivered_at: datetime | None = None
    created_at: datetime
