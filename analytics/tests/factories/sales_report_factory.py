"""Factories for SalesReport model."""

from datetime import timedelta
from decimal import Decimal

import factory
from django.utils import timezone as tz

from analytics.models import SalesReport
from analytics.models.choices import ReportType, TimePeriod
from core.tests.factories import UserFactory


class SalesReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SalesReport

    report_type = ReportType.SALES
    period = TimePeriod.DAILY
    period_start = factory.LazyFunction(
        lambda: tz.now().replace(hour=0, minute=0, second=0, microsecond=0)
    )
    period_end = factory.LazyAttribute(lambda obj: obj.period_start + timedelta(days=1))
    total_revenue = factory.Faker(
        "pydecimal", left_digits=5, right_digits=2, positive=True, min_value=Decimal("100.00")
    )
    total_orders = factory.Faker("random_int", min=1, max=100)
    total_items_sold = factory.Faker("random_int", min=1, max=300)
    average_order_value = factory.LazyAttribute(
        lambda obj: obj.total_revenue / obj.total_orders if obj.total_orders else Decimal("0.00")
    )
    total_discounts = Decimal("0.00")
    total_refunds = Decimal("0.00")
    total_tax = Decimal("0.00")
    total_shipping = Decimal("0.00")
    net_revenue = factory.LazyAttribute(lambda obj: obj.total_revenue - obj.total_refunds)
    new_customers = factory.Faker("random_int", min=0, max=20)
    returning_customers = factory.Faker("random_int", min=0, max=50)
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute("created_by")
