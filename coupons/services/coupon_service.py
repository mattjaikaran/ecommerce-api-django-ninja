"""Business logic for coupon validation and application."""

import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from api.exceptions import ValidationError
from core.models import Customer
from coupons.models import Coupon, CouponUsage
from coupons.models.choices import DiscountType

logger = logging.getLogger(__name__)


class CouponService:
    @staticmethod
    def get_by_code(code: str) -> Coupon:
        try:
            return Coupon.objects.get(code__iexact=code, is_deleted=False)
        except Coupon.DoesNotExist:
            raise ValidationError(f"Coupon '{code}' not found")

    @staticmethod
    def validate(coupon: Coupon, customer: Customer, order_subtotal: Decimal) -> None:
        now = timezone.now()

        if not coupon.is_active:
            raise ValidationError("This coupon is not active")

        if now < coupon.valid_from:
            raise ValidationError("This coupon is not yet valid")

        if now > coupon.valid_to:
            raise ValidationError("This coupon has expired")

        if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
            raise ValidationError("This coupon has reached its usage limit")

        if order_subtotal < coupon.min_order_amount:
            raise ValidationError(
                f"Minimum order amount of {coupon.min_order_amount} required for this coupon"
            )

        if coupon.customer_group_id and not customer.customer_groups.filter(pk=coupon.customer_group_id).exists():
            raise ValidationError("This coupon is not valid for your customer group")

        if coupon.restricted_customers.exists():
            if not coupon.restricted_customers.filter(pk=customer.pk).exists():
                raise ValidationError("This coupon is not valid for your account")

        if coupon.usage_limit_per_customer is not None:
            customer_uses = CouponUsage.objects.filter(
                coupon=coupon, customer=customer
            ).count()
            if customer_uses >= coupon.usage_limit_per_customer:
                raise ValidationError("You have already used this coupon the maximum number of times")

    @staticmethod
    def calculate_discount(coupon: Coupon, subtotal: Decimal) -> Decimal:
        if coupon.discount_type == DiscountType.PERCENTAGE:
            discount = (subtotal * coupon.discount_value / Decimal("100")).quantize(Decimal("0.01"))
            if coupon.max_discount_amount is not None:
                discount = min(discount, coupon.max_discount_amount)
            return discount

        if coupon.discount_type == DiscountType.FIXED_AMOUNT:
            return min(coupon.discount_value, subtotal)

        if coupon.discount_type == DiscountType.FREE_SHIPPING:
            return Decimal("0.00")

        return Decimal("0.00")

    @staticmethod
    def calculate_shipping_discount(coupon: Coupon, shipping_amount: Decimal) -> Decimal:
        if coupon.discount_type == DiscountType.FREE_SHIPPING:
            return shipping_amount
        return Decimal("0.00")

    @staticmethod
    @transaction.atomic
    def apply_to_order(coupon: Coupon, customer: Customer, order, request_user) -> Decimal:
        """Validate, record usage, and return the discount amount applied to order."""
        CouponService.validate(coupon, customer, order.subtotal)

        discount = CouponService.calculate_discount(coupon, order.subtotal)
        shipping_discount = CouponService.calculate_shipping_discount(coupon, order.shipping_amount)
        total_discount = discount + shipping_discount

        CouponUsage.objects.create(
            coupon=coupon,
            customer=customer,
            order=order,
            discount_applied=total_discount,
            created_by=request_user,
            updated_by=request_user,
        )

        coupon.used_count += 1
        coupon.save(update_fields=["used_count", "updated_at"])

        order.discount_amount = (order.discount_amount or Decimal("0.00")) + total_discount
        order.shipping_amount = max(Decimal("0.00"), order.shipping_amount - shipping_discount)
        order.total = max(
            Decimal("0.00"),
            order.subtotal + order.shipping_amount + order.tax_amount - order.discount_amount,
        )
        order.updated_by = request_user
        order.save()

        logger.info(
            "coupon_applied",
            extra={"coupon": coupon.code, "order": str(order.pk), "discount": str(total_discount)},
        )
        return total_discount

    @staticmethod
    @transaction.atomic
    def create_coupon(payload, request_user) -> Coupon:
        restricted_customers = payload.restricted_customer_ids or []
        coupon = Coupon.objects.create(
            code=payload.code.upper(),
            description=payload.description,
            discount_type=payload.discount_type,
            discount_value=payload.discount_value,
            max_discount_amount=payload.max_discount_amount,
            min_order_amount=payload.min_order_amount,
            usage_limit=payload.usage_limit,
            usage_limit_per_customer=payload.usage_limit_per_customer,
            valid_from=payload.valid_from,
            valid_to=payload.valid_to,
            is_active=payload.is_active,
            customer_group_id=payload.customer_group_id,
            created_by=request_user,
            updated_by=request_user,
        )
        if restricted_customers:
            coupon.restricted_customers.set(restricted_customers)
        return coupon

    @staticmethod
    @transaction.atomic
    def update_coupon(coupon: Coupon, payload, request_user) -> Coupon:
        updatable = [
            "description", "discount_type", "discount_value", "max_discount_amount",
            "min_order_amount", "usage_limit", "usage_limit_per_customer",
            "valid_from", "valid_to", "is_active", "customer_group_id",
        ]
        for field in updatable:
            value = getattr(payload, field, None)
            if value is not None:
                setattr(coupon, field, value)

        coupon.updated_by = request_user
        coupon.save()

        if payload.restricted_customer_ids is not None:
            coupon.restricted_customers.set(payload.restricted_customer_ids)

        return coupon
