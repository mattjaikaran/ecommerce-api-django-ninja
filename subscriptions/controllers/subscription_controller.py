from datetime import datetime
from decimal import Decimal
from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Schema
from ninja.pagination import paginate
from ninja_extra import api_controller, http_get, http_post
from ninja_extra.permissions import IsAuthenticated

from subscriptions.models import CustomerSubscription, SubscriptionPlan
from subscriptions.services import SubscriptionService


class SubscriptionPlanSchema(Schema):
    id: UUID
    name: str
    stripe_price_id: str
    stripe_product_id: str
    interval: str
    amount: Decimal
    currency: str
    features: list
    is_active: bool
    created_at: datetime


class CustomerSubscriptionSchema(Schema):
    id: UUID
    plan_id: UUID | None = None
    stripe_subscription_id: str
    stripe_customer_id: str
    status: str
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool
    canceled_at: datetime | None = None
    trial_end: datetime | None = None
    created_at: datetime


class CheckoutSchema(Schema):
    plan_id: UUID


class CheckoutResponseSchema(Schema):
    url: str


@api_controller("/subscription-plans", tags=["Subscriptions"])
class SubscriptionPlanController:
    @http_get("", response={200: list[SubscriptionPlanSchema]}, auth=None)
    @paginate
    def list_plans(self, request):
        return SubscriptionPlan.objects.filter(is_active=True)

    @http_get("/{plan_id}", response={200: SubscriptionPlanSchema}, auth=None)
    def get_plan(self, request, plan_id: str):
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)
        return 200, plan


@api_controller("/subscriptions", tags=["Subscriptions"])
class CustomerSubscriptionController:
    permission_classes = [IsAuthenticated]

    @http_get("/me", response={200: CustomerSubscriptionSchema})
    def get_my_subscription(self, request):
        customer = request.user.customer
        sub = SubscriptionService.get_active_subscription(customer)
        if sub is None:
            return 200, {}
        return 200, sub

    @http_post("/create-checkout", response={200: CheckoutResponseSchema})
    def create_checkout(self, request, payload: CheckoutSchema):
        customer = request.user.customer
        plan = get_object_or_404(SubscriptionPlan, id=payload.plan_id)
        url = SubscriptionService.create_checkout_session(customer, plan)
        return 200, CheckoutResponseSchema(url=url)

    @http_post("/{subscription_id}/cancel", response={200: CustomerSubscriptionSchema})
    def cancel_subscription(self, request, subscription_id: str):
        sub = get_object_or_404(CustomerSubscription, id=subscription_id)
        sub = SubscriptionService.cancel_subscription(sub)
        return 200, sub
