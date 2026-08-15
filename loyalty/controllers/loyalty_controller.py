from django.shortcuts import get_object_or_404
from ninja.security import django_auth
from ninja_extra import api_controller, http_get, http_post
from ninja_extra.pagination import PaginatedResponseSchema, paginate
from ninja_jwt.authentication import JWTAuth

from api.decorators import handle_exceptions, log_api_call
from api.exceptions import NotFoundError
from core.models import Customer
from loyalty.models import LoyaltyTransaction
from loyalty.schemas import (
    LoyaltyAccountSchema,
    LoyaltyRedeemSchema,
    LoyaltyTransactionSchema,
)
from loyalty.services import LoyaltyService
from orders.models import Order


@api_controller("/loyalty", tags=["Loyalty"], auth=[JWTAuth(), django_auth])
class LoyaltyController:
    @staticmethod
    def _get_customer(request) -> Customer:
        customer = Customer.objects.filter(user=request.user).first()
        if customer is None:
            raise NotFoundError("Customer not found")
        return customer

    @http_get(
        "/balance",
        response={200: LoyaltyAccountSchema, 401: dict, 403: dict, 404: dict},
    )
    @handle_exceptions()
    @log_api_call()
    def get_balance(self, request):
        customer = LoyaltyController._get_customer(request)
        account = LoyaltyService.get_account(customer)
        if account is None:
            raise NotFoundError("Loyalty account not found")
        return 200, account

    @http_get(
        "/transactions",
        response={
            200: PaginatedResponseSchema[LoyaltyTransactionSchema],
            401: dict,
            403: dict,
            404: dict,
        },
    )
    @handle_exceptions()
    @log_api_call()
    @paginate
    def list_transactions(self, request):
        customer = LoyaltyController._get_customer(request)
        account = LoyaltyService.get_account(customer)
        if account is None:
            raise NotFoundError("Loyalty account not found")
        return LoyaltyTransaction.objects.filter(account=account).order_by(
            "-created_at"
        )

    @http_post(
        "/redeem",
        response={
            201: LoyaltyTransactionSchema,
            400: dict,
            401: dict,
            403: dict,
            404: dict,
        },
    )
    @handle_exceptions()
    @log_api_call()
    def redeem_points(self, request, payload: LoyaltyRedeemSchema):
        customer = LoyaltyController._get_customer(request)
        order = None
        if payload.order_id:
            order = get_object_or_404(Order, id=payload.order_id, customer=customer)
        txn = LoyaltyService.redeem_points(customer, payload.points, order)
        return 201, txn
