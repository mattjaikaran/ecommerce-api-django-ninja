"""Payment and refund management controller."""

import logging
from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja_extra.pagination import PaginatedResponseSchema, paginate
from ninja.security import django_auth
from ninja_extra import api_controller, http_delete, http_get, http_post, http_put
from ninja_jwt.authentication import JWTAuth

from api.decorators import (
    create_endpoint,
    delete_endpoint,
    detail_endpoint,
    handle_exceptions,
    list_endpoint,
    log_api_call,
    update_endpoint,
)
from payments.models import PaymentMethod, PaymentRefund, PaymentTransaction
from payments.schemas import (
    PaymentMethodCreateSchema,
    PaymentMethodSchema,
    PaymentRefundCreateSchema,
    PaymentRefundSchema,
    PaymentTransactionSchema,
)

logger = logging.getLogger(__name__)


@api_controller("/payments", tags=["Payments"], auth=[JWTAuth(), django_auth])
class PaymentController:

    @http_get("/methods", response={200: PaginatedResponseSchema[PaymentMethodSchema], 401: dict, 403: dict})
    @handle_exceptions()
    @log_api_call()
    @paginate
    def list_payment_methods(self, request):
        return PaymentMethod.objects.select_related("customer__user").filter(
            is_active=True, customer__user=request.user
        ).order_by("-created_at")

    @http_get("/methods/{payment_method_id}", response={200: PaymentMethodSchema, 401: dict, 403: dict, 404: dict})
    @detail_endpoint(select_related=["customer__user"])
    def get_payment_method(self, request, payment_method_id: UUID):
        pm = get_object_or_404(PaymentMethod, id=payment_method_id, customer__user=request.user)
        return 200, pm

    @http_post("/methods", response={201: PaymentMethodSchema, 400: dict, 401: dict, 403: dict})
    @create_endpoint()
    def create_payment_method(self, request, payload: PaymentMethodCreateSchema):
        from payments.services import PaymentService
        pm = PaymentService.attach_payment_method(request.user, payload.stripe_payment_method_id, payload.is_default)
        return 201, pm

    @http_delete("/methods/{payment_method_id}", response={204: None, 401: dict, 403: dict, 404: dict})
    @delete_endpoint()
    def delete_payment_method(self, request, payment_method_id: UUID):
        pm = get_object_or_404(PaymentMethod, id=payment_method_id, customer__user=request.user)
        pm.is_active = False
        pm.deleted_by = request.user
        pm.save(update_fields=["is_active", "deleted_by"])
        return 204, None

    @http_put("/methods/{payment_method_id}/default", response={200: PaymentMethodSchema, 401: dict, 403: dict, 404: dict})
    @update_endpoint()
    def set_default_payment_method(self, request, payment_method_id: UUID):
        pm = get_object_or_404(PaymentMethod, id=payment_method_id, customer__user=request.user)
        PaymentMethod.objects.filter(customer__user=request.user).update(is_default=False)
        pm.is_default = True
        pm.save(update_fields=["is_default"])
        return 200, pm

    # Transactions (read-only for users)

    @http_get("/transactions", response={200: PaginatedResponseSchema[PaymentTransactionSchema], 401: dict, 403: dict})
    @handle_exceptions()
    @log_api_call()
    @paginate
    def list_transactions(self, request):
        return PaymentTransaction.objects.select_related(
            "order", "payment_method"
        ).filter(order__customer__user=request.user).order_by("-created_at")

    @http_get("/transactions/{transaction_id}", response={200: PaymentTransactionSchema, 401: dict, 403: dict, 404: dict})
    @detail_endpoint(select_related=["order", "payment_method"])
    def get_transaction(self, request, transaction_id: UUID):
        txn = get_object_or_404(PaymentTransaction, id=transaction_id, order__customer__user=request.user)
        return 200, txn

    # Refunds

    @http_post("/transactions/{transaction_id}/refund", response={201: PaymentRefundSchema, 400: dict, 401: dict, 403: dict, 404: dict})
    @create_endpoint()
    def create_refund(self, request, transaction_id: UUID, payload: PaymentRefundCreateSchema):
        from payments.services import PaymentService
        txn = get_object_or_404(PaymentTransaction, id=transaction_id)
        refund = PaymentService.create_refund(txn, payload.amount, payload.reason, payload.notes, request.user)
        return 201, refund

    @http_get("/transactions/{transaction_id}/refunds", response={200: list[PaymentRefundSchema], 401: dict, 403: dict})
    @list_endpoint(
        select_related=["transaction__order"],
        filter_fields={"status": "exact"},
        ordering_fields=["created_at"],
    )
    def list_refunds(self, request, transaction_id: UUID):
        return 200, PaymentRefund.objects.filter(transaction_id=transaction_id)
