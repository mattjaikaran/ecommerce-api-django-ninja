from datetime import timedelta
from decimal import Decimal

import factory
from django.utils import timezone

from coupons.models import Coupon, CouponUsage
from coupons.models.choices import DiscountType
from core.tests.factories import CustomerFactory, UserFactory


class CouponFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Coupon

    code = factory.Sequence(lambda n: f"SAVE{n:04d}")
    description = factory.Faker("sentence")
    discount_type = DiscountType.PERCENTAGE
    discount_value = Decimal("10.00")
    max_discount_amount = None
    min_order_amount = Decimal("0.00")
    usage_limit = None
    usage_limit_per_customer = None
    used_count = 0
    valid_from = factory.LazyFunction(lambda: timezone.now() - timedelta(days=1))
    valid_to = factory.LazyFunction(lambda: timezone.now() + timedelta(days=30))
    is_active = True
    customer_group = None
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute("created_by")


class FixedAmountCouponFactory(CouponFactory):
    discount_type = DiscountType.FIXED_AMOUNT
    discount_value = Decimal("5.00")


class FreeShippingCouponFactory(CouponFactory):
    discount_type = DiscountType.FREE_SHIPPING
    discount_value = Decimal("0.00")


class ExpiredCouponFactory(CouponFactory):
    valid_from = factory.LazyFunction(lambda: timezone.now() - timedelta(days=60))
    valid_to = factory.LazyFunction(lambda: timezone.now() - timedelta(days=1))


class InactiveCouponFactory(CouponFactory):
    is_active = False


class LimitedCouponFactory(CouponFactory):
    usage_limit = 5
    used_count = 4


class CouponUsageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CouponUsage

    coupon = factory.SubFactory(CouponFactory)
    customer = factory.SubFactory(CustomerFactory)
    order = None
    discount_applied = Decimal("10.00")
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute("created_by")
