from django.db import transaction
from django.shortcuts import get_object_or_404
from ninja.pagination import paginate
from ninja_extra import (
    api_controller,
    http_delete,
    http_get,
    http_post,
    http_put,
)
from ninja_extra.permissions import IsAuthenticated

from api.decorators import handle_exceptions, log_api_call
from api.exceptions import BadRequestError
from orders.models import (
    FulfillmentLineItem,
    FulfillmentOrder,
    FulfillmentStatus,
    Order,
    OrderStatus,
)
from orders.schemas import (
    FulfillmentCreateSchema,
    FulfillmentSchema,
    FulfillmentUpdateSchema,
)


@api_controller("/fulfillments", tags=["Order Fulfillments"])
class FulfillmentController:
    permission_classes = [IsAuthenticated]

    @http_get("", response={200: list[FulfillmentSchema]})
    @handle_exceptions
    @log_api_call()
    @paginate
    def list_fulfillments(self, request):
        """Get paginated list of fulfillments."""
        fulfillments = (
            FulfillmentOrder.objects.select_related("order")
            .prefetch_related("items")
            .order_by("-created_at")
        )
        return 200, fulfillments

    @http_get("/{fulfillment_id}", response={200: FulfillmentSchema})
    @handle_exceptions
    @log_api_call()
    def get_fulfillment(self, request, fulfillment_id: str):
        """Get single fulfillment by ID."""
        fulfillment = get_object_or_404(
            FulfillmentOrder.objects.select_related("order").prefetch_related("items"),
            id=fulfillment_id,
        )
        return 200, fulfillment

    @http_post("", response={201: FulfillmentSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def create_fulfillment(self, request, payload: FulfillmentCreateSchema):
        """Create new fulfillment."""
        order = get_object_or_404(Order, id=payload.order_id)

        # Validate order state
        if order.status not in [OrderStatus.PENDING, OrderStatus.PARTIALLY_SHIPPED]:
            raise BadRequestError("Order cannot be fulfilled in its current status")

        # Create fulfillment
        fulfillment = FulfillmentOrder.objects.create(
            order=order,
            status=FulfillmentStatus.PENDING,
            tracking_number=payload.tracking_number,
            tracking_url=payload.tracking_url,
            shipping_carrier=payload.shipping_carrier,
            shipping_method=payload.shipping_method,
            shipping_label_url=payload.shipping_label_url,
            notes=payload.notes,
            meta_data=payload.meta_data,
        )

        # Create fulfillment items
        for item in payload.items:
            order_item = order.items.get(id=item["order_item_id"])

            # Validate quantity
            if item["quantity"] > order_item.quantity - order_item.fulfilled_quantity:
                raise BadRequestError(
                    f"Invalid fulfillment quantity. Requested {item['quantity']} "
                    f"exceeds available {order_item.quantity - order_item.fulfilled_quantity} "
                    f"for item {order_item.id}"
                )

            FulfillmentLineItem.objects.create(
                fulfillment=fulfillment,
                order_item=order_item,
                quantity=item["quantity"],
            )

            # Update order item fulfilled quantity
            order_item.fulfilled_quantity += item["quantity"]
            order_item.save()

        # Update order status if all items are fulfilled
        from orders.services import OrderService

        if all(item.quantity == item.fulfilled_quantity for item in order.items.all()):
            OrderService.transition_order(
                order,
                OrderStatus.SHIPPED,
                request.user,
                notes="Fulfillment created",
            )
        else:
            OrderService.transition_order(
                order,
                OrderStatus.PARTIALLY_SHIPPED,
                request.user,
                notes="Fulfillment created",
            )

        return 201, fulfillment

    @http_put("/{fulfillment_id}", response={200: FulfillmentSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def update_fulfillment(
        self, request, fulfillment_id: str, payload: FulfillmentUpdateSchema
    ):
        """Update existing fulfillment."""
        fulfillment = get_object_or_404(FulfillmentOrder, id=fulfillment_id)

        # Only allow updates if fulfillment is in an editable state
        if fulfillment.status not in [
            FulfillmentStatus.PENDING,
            FulfillmentStatus.PROCESSING,
        ]:
            raise BadRequestError("Fulfillment cannot be updated in its current status")

        # Update fulfillment fields
        for field, value in payload.dict(exclude_unset=True).items():
            setattr(fulfillment, field, value)
        fulfillment.save()

        # If status is updated to SHIPPED, update order status
        from orders.services import OrderService

        if payload.status == FulfillmentStatus.SHIPPED:
            order = fulfillment.order
            if all(
                f.status == FulfillmentStatus.SHIPPED for f in order.fulfillments.all()
            ):
                OrderService.transition_order(
                    order,
                    OrderStatus.SHIPPED,
                    request.user,
                    notes="Fulfillment shipped",
                )

        return 200, fulfillment

    @http_delete("/{fulfillment_id}", response={204: None})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def delete_fulfillment(self, request, fulfillment_id: str):
        """Delete fulfillment."""
        fulfillment = get_object_or_404(FulfillmentOrder, id=fulfillment_id)

        # Only allow deletion of pending fulfillments
        if fulfillment.status != FulfillmentStatus.PENDING:
            raise BadRequestError("Only pending fulfillments can be deleted")

        # Restore order item fulfilled quantities
        for item in fulfillment.items.all():
            order_item = item.order_item
            order_item.fulfilled_quantity -= item.quantity
            order_item.save()

        # Update order status
        from orders.services import OrderService

        order = fulfillment.order
        if order.status in [OrderStatus.SHIPPED, OrderStatus.PARTIALLY_SHIPPED]:
            if any(item.fulfilled_quantity > 0 for item in order.items.all()):
                OrderService.transition_order(
                    order,
                    OrderStatus.PARTIALLY_SHIPPED,
                    request.user,
                    notes="Fulfillment deleted",
                )
            else:
                OrderService.transition_order(
                    order,
                    OrderStatus.PENDING,
                    request.user,
                    notes="Fulfillment deleted",
                )

        fulfillment.delete()
        return 204, None

    @http_post("/{fulfillment_id}/ship", response={200: FulfillmentSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def ship_fulfillment(self, request, fulfillment_id: str):
        """Mark fulfillment as shipped."""
        fulfillment = get_object_or_404(FulfillmentOrder, id=fulfillment_id)

        # Validate fulfillment state
        if fulfillment.status != FulfillmentStatus.PENDING:
            raise BadRequestError("Only pending fulfillments can be shipped")

        if not fulfillment.tracking_number:
            raise BadRequestError("Tracking number is required to ship fulfillment")

        # Update fulfillment status
        fulfillment.status = FulfillmentStatus.SHIPPED
        fulfillment.save()

        # Update order status
        from orders.services import OrderService

        order = fulfillment.order
        if all(f.status == FulfillmentStatus.SHIPPED for f in order.fulfillments.all()):
            OrderService.transition_order(
                order,
                OrderStatus.SHIPPED,
                request.user,
                notes="Fulfillment shipped",
            )

        return 200, fulfillment

    @http_post("/{fulfillment_id}/cancel", response={200: FulfillmentSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def cancel_fulfillment(self, request, fulfillment_id: str):
        """Cancel fulfillment."""
        fulfillment = get_object_or_404(FulfillmentOrder, id=fulfillment_id)

        # Validate fulfillment state
        if fulfillment.status not in [
            FulfillmentStatus.PENDING,
            FulfillmentStatus.PROCESSING,
        ]:
            raise BadRequestError(
                "Fulfillment cannot be cancelled in its current status"
            )

        # Update fulfillment status
        fulfillment.status = FulfillmentStatus.CANCELLED
        fulfillment.save()

        # Restore order item fulfilled quantities
        for item in fulfillment.items.all():
            order_item = item.order_item
            order_item.fulfilled_quantity -= item.quantity
            order_item.save()

        # Update order status
        from orders.services import OrderService

        order = fulfillment.order
        if any(item.fulfilled_quantity > 0 for item in order.items.all()):
            OrderService.transition_order(
                order,
                OrderStatus.PARTIALLY_SHIPPED,
                request.user,
                notes="Fulfillment cancelled",
            )
        else:
            OrderService.transition_order(
                order,
                OrderStatus.PENDING,
                request.user,
                notes="Fulfillment cancelled",
            )

        return 200, fulfillment
