from decimal import Decimal

from django.shortcuts import get_object_or_404
from ninja.pagination import paginate
from ninja_extra import api_controller, http_delete, http_get, http_post, http_put
from ninja_extra.permissions import IsAuthenticated

from api.decorators import handle_exceptions, log_api_call
from api.exceptions import ValidationError
from coupons.models import Coupon, CouponUsage
from coupons.schemas import (
    ApplyCouponSchema,
    CouponCreateSchema,
    CouponSchema,
    CouponUpdateSchema,
    CouponUsageSchema,
    CouponValidateResponseSchema,
    CouponValidateSchema,
)
from coupons.services import CouponService
from orders.models import Order


@api_controller("/coupons", tags=["Coupons"])
class CouponController:
    permission_classes = [IsAuthenticated]

    @http_get("", response={200: list[CouponSchema]})
    @handle_exceptions
    @log_api_call()
    @paginate
    def list_coupons(self, request, is_active: bool | None = None):
        qs = Coupon.objects.filter(is_deleted=False)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        return qs.order_by("-created_at")

    @http_get("/{coupon_id}", response={200: CouponSchema})
    @handle_exceptions
    @log_api_call()
    def get_coupon(self, request, coupon_id: str):
        coupon = get_object_or_404(Coupon, id=coupon_id, is_deleted=False)
        return 200, coupon

    @http_post("", response={201: CouponSchema})
    @handle_exceptions
    @log_api_call()
    def create_coupon(self, request, payload: CouponCreateSchema):
        if Coupon.objects.filter(code=payload.code.upper(), is_deleted=False).exists():
            raise ValidationError(f"Coupon code '{payload.code}' already exists")
        coupon = CouponService.create_coupon(payload, request.user)
        return 201, coupon

    @http_put("/{coupon_id}", response={200: CouponSchema})
    @handle_exceptions
    @log_api_call()
    def update_coupon(self, request, coupon_id: str, payload: CouponUpdateSchema):
        coupon = get_object_or_404(Coupon, id=coupon_id, is_deleted=False)
        coupon = CouponService.update_coupon(coupon, payload, request.user)
        return 200, coupon

    @http_delete("/{coupon_id}", response={204: None})
    @handle_exceptions
    @log_api_call()
    def delete_coupon(self, request, coupon_id: str):
        coupon = get_object_or_404(Coupon, id=coupon_id, is_deleted=False)
        coupon.is_deleted = True
        coupon.is_active = False
        coupon.updated_by = request.user
        coupon.save(update_fields=["is_deleted", "is_active", "updated_at", "updated_by"])
        return 204, None

    @http_post("/validate", response={200: CouponValidateResponseSchema})
    @handle_exceptions
    @log_api_call()
    def validate_coupon(self, request, payload: CouponValidateSchema):
        """Preview the discount without consuming the coupon."""
        try:
            coupon = CouponService.get_by_code(payload.code)
            customer = request.user.customer
            CouponService.validate(coupon, customer, payload.order_subtotal)
            discount = CouponService.calculate_discount(coupon, payload.order_subtotal)
            shipping_discount = CouponService.calculate_shipping_discount(coupon, Decimal("0"))
            return 200, CouponValidateResponseSchema(
                valid=True,
                discount_amount=discount,
                shipping_discount=shipping_discount,
                message="Coupon is valid",
            )
        except ValidationError as e:
            return 200, CouponValidateResponseSchema(
                valid=False,
                discount_amount=Decimal("0"),
                shipping_discount=Decimal("0"),
                message=str(e),
            )

    @http_post("/apply", response={200: dict})
    @handle_exceptions
    @log_api_call()
    def apply_coupon(self, request, payload: ApplyCouponSchema):
        """Apply a coupon to an existing order."""
        order = get_object_or_404(Order, id=payload.order_id)
        coupon = CouponService.get_by_code(payload.code)
        customer = request.user.customer

        if CouponUsage.objects.filter(coupon=coupon, order=order).exists():
            raise ValidationError("This coupon has already been applied to this order")

        discount = CouponService.apply_to_order(coupon, customer, order, request.user)
        return 200, {
            "message": "Coupon applied successfully",
            "discount_applied": str(discount),
            "new_total": str(order.total),
        }

    @http_get("/{coupon_id}/usages", response={200: list[CouponUsageSchema]})
    @handle_exceptions
    @log_api_call()
    @paginate
    def get_coupon_usages(self, request, coupon_id: str):
        coupon = get_object_or_404(Coupon, id=coupon_id, is_deleted=False)
        return CouponUsage.objects.filter(coupon=coupon).select_related(
            "customer", "order"
        ).order_by("-created_at")
