"""Tests for CouponService business logic."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from api.exceptions import ValidationError
from coupons.models import CouponUsage
from coupons.models.choices import DiscountType
from coupons.services import CouponService
from coupons.tests.factories.coupon_factory import (
    CouponFactory,
    CouponUsageFactory,
    ExpiredCouponFactory,
    FixedAmountCouponFactory,
    FreeShippingCouponFactory,
    InactiveCouponFactory,
    LimitedCouponFactory,
)
from core.tests.factories import CustomerFactory

pytestmark = pytest.mark.django_db


class TestGetByCode:
    def test_found(self):
        coupon = CouponFactory(code="HELLO10")
        result = CouponService.get_by_code("hello10")
        assert result.pk == coupon.pk

    def test_not_found(self):
        with pytest.raises(ValidationError):
            CouponService.get_by_code("NOPE")

    def test_soft_deleted_not_found(self):
        coupon = CouponFactory(code="GONE", is_deleted=True)
        with pytest.raises(ValidationError):
            CouponService.get_by_code("GONE")


class TestValidate:
    def test_inactive_raises(self):
        coupon = InactiveCouponFactory()
        customer = CustomerFactory()
        with pytest.raises(ValidationError, match="not active"):
            CouponService.validate(coupon, customer, Decimal("100"))

    def test_not_yet_valid_raises(self):
        coupon = CouponFactory(valid_from=timezone.now() + timedelta(days=1))
        customer = CustomerFactory()
        with pytest.raises(ValidationError, match="not yet valid"):
            CouponService.validate(coupon, customer, Decimal("100"))

    def test_expired_raises(self):
        coupon = ExpiredCouponFactory()
        customer = CustomerFactory()
        with pytest.raises(ValidationError, match="expired"):
            CouponService.validate(coupon, customer, Decimal("100"))

    def test_usage_limit_reached_raises(self):
        coupon = LimitedCouponFactory(usage_limit=5, used_count=5)
        customer = CustomerFactory()
        with pytest.raises(ValidationError, match="usage limit"):
            CouponService.validate(coupon, customer, Decimal("100"))

    def test_min_order_amount_not_met_raises(self):
        coupon = CouponFactory(min_order_amount=Decimal("50.00"))
        customer = CustomerFactory()
        with pytest.raises(ValidationError, match="Minimum order amount"):
            CouponService.validate(coupon, customer, Decimal("30.00"))

    def test_customer_group_mismatch_raises(self):
        from core.tests.factories import CustomerGroupFactory
        group = CustomerGroupFactory()
        coupon = CouponFactory(customer_group=group)
        customer = CustomerFactory()
        with pytest.raises(ValidationError, match="customer group"):
            CouponService.validate(coupon, customer, Decimal("100"))

    def test_per_customer_limit_raises(self):
        coupon = CouponFactory(usage_limit_per_customer=1)
        customer = CustomerFactory()
        CouponUsageFactory(coupon=coupon, customer=customer)
        with pytest.raises(ValidationError, match="maximum number of times"):
            CouponService.validate(coupon, customer, Decimal("100"))

    def test_valid_passes(self):
        coupon = CouponFactory(min_order_amount=Decimal("10.00"))
        customer = CustomerFactory()
        CouponService.validate(coupon, customer, Decimal("100"))


class TestCalculateDiscount:
    def test_percentage(self):
        coupon = CouponFactory(discount_type=DiscountType.PERCENTAGE, discount_value=Decimal("10"))
        assert CouponService.calculate_discount(coupon, Decimal("100")) == Decimal("10.00")

    def test_percentage_capped_by_max(self):
        coupon = CouponFactory(
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("50"),
            max_discount_amount=Decimal("20.00"),
        )
        assert CouponService.calculate_discount(coupon, Decimal("200")) == Decimal("20.00")

    def test_fixed_amount(self):
        coupon = FixedAmountCouponFactory(discount_value=Decimal("5.00"))
        assert CouponService.calculate_discount(coupon, Decimal("50")) == Decimal("5.00")

    def test_fixed_amount_capped_by_subtotal(self):
        coupon = FixedAmountCouponFactory(discount_value=Decimal("200.00"))
        assert CouponService.calculate_discount(coupon, Decimal("50")) == Decimal("50.00")

    def test_free_shipping_returns_zero(self):
        coupon = FreeShippingCouponFactory()
        assert CouponService.calculate_discount(coupon, Decimal("100")) == Decimal("0.00")


class TestCalculateShippingDiscount:
    def test_free_shipping(self):
        coupon = FreeShippingCouponFactory()
        assert CouponService.calculate_shipping_discount(coupon, Decimal("9.99")) == Decimal("9.99")

    def test_non_free_shipping_returns_zero(self):
        coupon = CouponFactory()
        assert CouponService.calculate_shipping_discount(coupon, Decimal("9.99")) == Decimal("0.00")


class TestCreateCoupon:
    def test_creates_and_uppercases_code(self):
        from core.tests.factories import UserFactory
        user = UserFactory()

        class Payload:
            code = "hello20"
            description = "20% off"
            discount_type = DiscountType.PERCENTAGE
            discount_value = Decimal("20")
            max_discount_amount = None
            min_order_amount = Decimal("0")
            usage_limit = None
            usage_limit_per_customer = None
            valid_from = timezone.now()
            valid_to = timezone.now() + timedelta(days=30)
            is_active = True
            customer_group_id = None
            restricted_customer_ids = []

        coupon = CouponService.create_coupon(Payload(), user)
        assert coupon.code == "HELLO20"
        assert coupon.created_by == user


class TestApplyToOrder:
    def _make_order(self, subtotal=Decimal("100"), shipping=Decimal("10")):
        from orders.tests.factories import OrderFactory
        return OrderFactory(
            subtotal=subtotal,
            shipping_amount=shipping,
            discount_amount=Decimal("0"),
            tax_amount=Decimal("0"),
            total=subtotal + shipping,
        )

    def test_applies_percentage_discount(self):
        coupon = CouponFactory(discount_value=Decimal("10"))
        order = self._make_order()
        customer = order.customer
        user = order.customer.user
        discount = CouponService.apply_to_order(coupon, customer, order, user)
        assert discount == Decimal("10.00")
        order.refresh_from_db()
        assert order.discount_amount == Decimal("10.00")
        assert order.total == Decimal("100.00")

    def test_records_usage(self):
        coupon = CouponFactory()
        order = self._make_order()
        customer = order.customer
        user = order.customer.user
        CouponService.apply_to_order(coupon, customer, order, user)
        assert CouponUsage.objects.filter(coupon=coupon, order=order).count() == 1

    def test_increments_used_count(self):
        coupon = CouponFactory(used_count=0)
        order = self._make_order()
        customer = order.customer
        user = order.customer.user
        CouponService.apply_to_order(coupon, customer, order, user)
        coupon.refresh_from_db()
        assert coupon.used_count == 1

    def test_free_shipping_removes_shipping_cost(self):
        coupon = FreeShippingCouponFactory()
        order = self._make_order(subtotal=Decimal("100"), shipping=Decimal("10"))
        customer = order.customer
        user = order.customer.user
        discount = CouponService.apply_to_order(coupon, customer, order, user)
        assert discount == Decimal("10.00")
        order.refresh_from_db()
        assert order.shipping_amount == Decimal("0.00")

    def test_invalid_coupon_raises_and_does_not_record_usage(self):
        coupon = ExpiredCouponFactory()
        order = self._make_order()
        customer = order.customer
        user = order.customer.user
        with pytest.raises(ValidationError):
            CouponService.apply_to_order(coupon, customer, order, user)
        assert CouponUsage.objects.filter(coupon=coupon).count() == 0
