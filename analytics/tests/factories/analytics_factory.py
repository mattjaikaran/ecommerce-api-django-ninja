"""Factories for CustomerAnalytics, ProductAnalytics, PerformanceMetric."""

from datetime import timedelta
from decimal import Decimal

import factory
from django.utils import timezone as tz

from analytics.models import CustomerAnalytics, PerformanceMetric, ProductAnalytics
from analytics.models.choices import MetricType, TimePeriod
from core.tests.factories import CustomerFactory, UserFactory
from products.tests.factories import ProductFactory


class CustomerAnalyticsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomerAnalytics

    customer = factory.SubFactory(CustomerFactory)
    period = TimePeriod.MONTHLY
    period_start = factory.LazyFunction(
        lambda: tz.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    )
    period_end = factory.LazyAttribute(
        lambda obj: (
            obj.period_start.replace(month=obj.period_start.month % 12 + 1)
            if obj.period_start.month < 12
            else obj.period_start.replace(year=obj.period_start.year + 1, month=1)
        )
    )
    total_orders = factory.Faker("random_int", min=1, max=20)
    total_spent = factory.Faker(
        "pydecimal", left_digits=4, right_digits=2, positive=True, min_value=Decimal("10.00")
    )
    average_order_value = factory.LazyAttribute(
        lambda obj: obj.total_spent / obj.total_orders if obj.total_orders else Decimal("0.00")
    )
    total_returns = factory.Faker("random_int", min=0, max=3)
    lifetime_value = factory.LazyAttribute(lambda obj: obj.total_spent)
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute("created_by")


class ProductAnalyticsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductAnalytics

    product = factory.SubFactory(ProductFactory)
    period = TimePeriod.DAILY
    period_start = factory.LazyFunction(
        lambda: tz.now().replace(hour=0, minute=0, second=0, microsecond=0)
    )
    period_end = factory.LazyAttribute(lambda obj: obj.period_start + timedelta(days=1))
    units_sold = factory.Faker("random_int", min=0, max=50)
    revenue = factory.Faker(
        "pydecimal", left_digits=4, right_digits=2, positive=True, min_value=Decimal("1.00")
    )
    views = factory.Faker("random_int", min=0, max=500)
    conversion_rate = Decimal("0.00")
    returns = factory.Faker("random_int", min=0, max=5)
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute("created_by")


class PerformanceMetricFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PerformanceMetric

    metric_type = MetricType.REVENUE
    period = TimePeriod.DAILY
    period_start = factory.LazyFunction(
        lambda: tz.now().replace(hour=0, minute=0, second=0, microsecond=0)
    )
    period_end = factory.LazyAttribute(lambda obj: obj.period_start + timedelta(days=1))
    value = factory.Faker(
        "pydecimal", left_digits=6, right_digits=4, positive=True, min_value=Decimal("1.00")
    )
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute("created_by")
