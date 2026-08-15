from django.db import transaction
from django.shortcuts import get_object_or_404
from ninja.pagination import paginate
from ninja_extra import (
    api_controller,
    http_get,
    http_post,
    http_put,
)
from ninja_extra.permissions import IsAuthenticated

from api.decorators import handle_exceptions, log_api_call
from api.exceptions import BadRequestError
from orders.models import (
    Order,
    OrderStatus,
    PaymentStatus,
    PaymentTransaction,
    Refund,
    RefundStatus,
)
from orders.schemas import (
    PaymentTransactionSchema,
    RefundCreateSchema,
    RefundSchema,
    RefundUpdateSchema,
)

from orders.services import OrderService


@api_controller("/payments", tags=["Order Payments"])
class PaymentController:
    permission_classes = [IsAuthenticated]

    @http_get("", response={200: list[PaymentTransactionSchema]})
    @handle_exceptions
    @log_api_call()
    @paginate
    def list_payments(self, request):
        """Get paginated list of payment transactions."""
        payments = PaymentTransaction.objects.select_related("order").order_by(
            "-created_at"
        )
        return 200, payments

    @http_get("/{payment_id}", response={200: PaymentTransactionSchema})
    @handle_exceptions
    @log_api_call()
    def get_payment(self, request, payment_id: str):
        """Get single payment transaction by ID."""
        payment = get_object_or_404(
            PaymentTransaction.objects.select_related("order"), id=payment_id
        )
        return 200, payment

    @http_post("/authorize", response={201: PaymentTransactionSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def authorize_payment(
        self, request, order_id: str, amount: float, payment_method: str, gateway: str
    ):
        """Authorize payment for an order."""
        order = get_object_or_404(Order, id=order_id)

        # Validate order state
        if order.status != OrderStatus.PENDING:
            raise BadRequestError("Order cannot be authorized in its current status")

        if order.payment_status != PaymentStatus.PENDING:
            raise BadRequestError("Payment has already been processed")

        # Create payment transaction
        payment = PaymentTransaction.objects.create(
            order=order,
            transaction_id=f"AUTH_{order.order_number}",  # Replace with actual gateway transaction ID
            payment_method=payment_method,
            amount=amount,
            currency=order.currency,
            status=PaymentStatus.AUTHORIZED,
            gateway=gateway,
            gateway_response={},  # Replace with actual gateway response
        )

        # Update order payment status
        order.payment_status = PaymentStatus.AUTHORIZED
        order.payment_method = payment_method
        order.payment_gateway = gateway
        order.payment_gateway_id = payment.transaction_id
        order.save()

        return 201, payment

    @http_post("/capture/{payment_id}", response={200: PaymentTransactionSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def capture_payment(self, request, payment_id: str, amount: float = None):
        """Capture an authorized payment."""
        payment = get_object_or_404(PaymentTransaction, id=payment_id)
        order = payment.order

        # Validate payment state
        if payment.status != PaymentStatus.AUTHORIZED:
            raise BadRequestError("Payment must be authorized before capture")

        # Use authorized amount if no capture amount specified
        capture_amount = amount or payment.amount

        if capture_amount > payment.amount:
            raise BadRequestError("Capture amount cannot exceed authorized amount")

        # Update payment transaction
        payment.status = PaymentStatus.PAID
        payment.amount = capture_amount
        payment.gateway_response = {}  # Replace with actual gateway response
        payment.save()

        # Update order payment status
        order.payment_status = PaymentStatus.PAID
        order.save()

        return 200, payment

    @http_post("/void/{payment_id}", response={200: PaymentTransactionSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def void_payment(self, request, payment_id: str):
        """Void an authorized payment."""
        payment = get_object_or_404(PaymentTransaction, id=payment_id)
        order = payment.order

        # Validate payment state
        if payment.status != PaymentStatus.AUTHORIZED:
            raise BadRequestError("Only authorized payments can be voided")

        # Update payment transaction
        payment.status = PaymentStatus.VOIDED
        payment.gateway_response = {}  # Replace with actual gateway response
        payment.save()

        # Update order payment status
        order.payment_status = PaymentStatus.VOIDED
        order.save()

        return 200, payment

    @http_get("/refunds", response={200: list[RefundSchema]})
    @handle_exceptions
    @log_api_call()
    @paginate
    def list_refunds(self, request):
        """Get paginated list of refunds."""
        refunds = Refund.objects.select_related("order").order_by("-created_at")
        return 200, refunds

    @http_get("/refunds/{refund_id}", response={200: RefundSchema})
    @handle_exceptions
    @log_api_call()
    def get_refund(self, request, refund_id: str):
        """Get single refund by ID."""
        refund = get_object_or_404(Refund.objects.select_related("order"), id=refund_id)
        return 200, refund

    @http_post("/refunds", response={201: RefundSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def create_refund(self, request, payload: RefundCreateSchema):
        """Create new refund."""
        order = get_object_or_404(Order, id=payload.order_id)

        # Validate order state
        if order.status not in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            raise BadRequestError("Order cannot be refunded in its current status")

        if order.payment_status != PaymentStatus.PAID:
            raise BadRequestError("Order must be paid before refund")

        # Validate refund amount
        total_refunded = sum(r.amount for r in order.refunds.all())
        if total_refunded + payload.amount > order.total:
            raise BadRequestError("Refund amount exceeds order total")

        # Create refund
        refund = Refund.objects.create(
            order=order,
            transaction_id=payload.transaction_id,
            amount=payload.amount,
            status=RefundStatus.PENDING,
            reason=payload.reason,
            notes=payload.notes,
            meta_data=payload.meta_data,
        )

        # Update order payment status
        if total_refunded + payload.amount == order.total:
            order.payment_status = PaymentStatus.REFUNDED
            OrderService.transition_order(
                order,
                OrderStatus.REFUNDED,
                request.user,
                notes="Full refund issued",
            )
        else:
            order.payment_status = PaymentStatus.PARTIALLY_REFUNDED
            OrderService.transition_order(
                order,
                OrderStatus.PARTIALLY_REFUNDED,
                request.user,
                notes="Partial refund issued",
            )
        order.save(update_fields=["payment_status", "updated_at"])

        return 201, refund

    @http_put("/refunds/{refund_id}", response={200: RefundSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def update_refund(self, request, refund_id: str, payload: RefundUpdateSchema):
        """Update existing refund."""
        refund = get_object_or_404(Refund, id=refund_id)

        # Only allow updates if refund is in an editable state
        if refund.status not in [RefundStatus.PENDING, RefundStatus.PROCESSING]:
            raise BadRequestError("Refund cannot be updated in its current status")

        # Update refund fields
        for field, value in payload.dict(exclude_unset=True).items():
            setattr(refund, field, value)
        refund.save()

        return 200, refund

    @http_post("/refunds/{refund_id}/process", response={200: RefundSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def process_refund(self, request, refund_id: str):
        """Process a pending refund."""
        refund = get_object_or_404(Refund, id=refund_id)

        # Validate refund state
        if refund.status != RefundStatus.PENDING:
            raise BadRequestError("Only pending refunds can be processed")

        # Process refund with payment gateway
        # Replace with actual gateway integration
        refund.status = RefundStatus.COMPLETED
        refund.refund_transaction_id = f"REF_{refund.order.order_number}"
        refund.gateway_response = {}  # Replace with actual gateway response
        refund.save()

        return 200, refund
