"""Tests for analytics models."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone as tz

from analytics.models import CustomerAnalytics, PerformanceMetric, ProductAnalytics, SalesReport
from analytics.models.choices import MetricType, ReportType, TimePeriod
from analytics.tests.factories import (
    CustomerAnalyticsFactory,
    PerformanceMetricFactory,
    ProductAnalyticsFactory,
    SalesReportFactory,
)

pytestmark = pytest.mark.django_db


class TestSalesReport:
    def test_create(self):
        report = SalesReportFactory()
        assert report.pk is not None
        assert report.report_type == ReportType.SALES
        assert report.period == TimePeriod.DAILY
        assert report.total_revenue > 0
        assert report.period_end > report.period_start

    def test_str(self):
        report = SalesReportFactory()
        start = report.period_start.strftime("%Y-%m-%d")
        end = report.period_end.strftime("%Y-%m-%d")
        assert start in str(report)
        assert end in str(report)

    def test_net_revenue_calculation(self):
        report = SalesReportFactory(
            total_revenue=Decimal("1000.00"),
            total_refunds=Decimal("50.00"),
            net_revenue=Decimal("950.00"),
        )
        assert report.net_revenue == Decimal("950.00")

    def test_ordering(self):
        now = tz.now()
        older = SalesReportFactory(
            period_start=now - timedelta(days=2),
            period_end=now - timedelta(days=1),
        )
        newer = SalesReportFactory(
            period_start=now - timedelta(days=1),
            period_end=now,
        )
        reports = list(SalesReport.objects.all())
        assert reports[0].pk == newer.pk
        assert reports[1].pk == older.pk

    def test_filter_by_type(self):
        SalesReportFactory(report_type=ReportType.SALES)
        SalesReportFactory(report_type=ReportType.CUSTOMER)
        assert SalesReport.objects.filter(report_type=ReportType.SALES).count() == 1
        assert SalesReport.objects.filter(report_type=ReportType.CUSTOMER).count() == 1


class TestCustomerAnalytics:
    def test_create(self):
        analytics = CustomerAnalyticsFactory()
        assert analytics.pk is not None
        assert analytics.customer is not None
        assert analytics.total_spent > 0

    def test_str(self):
        analytics = CustomerAnalyticsFactory()
        s = str(analytics)
        assert str(analytics.customer_id) in s

    def test_average_order_value(self):
        analytics = CustomerAnalyticsFactory(
            total_orders=4,
            total_spent=Decimal("400.00"),
            average_order_value=Decimal("100.00"),
        )
        assert analytics.average_order_value == Decimal("100.00")

    def test_customer_cascade_delete(self):
        analytics = CustomerAnalyticsFactory()
        customer = analytics.customer
        customer.delete()
        assert not CustomerAnalytics.objects.filter(pk=analytics.pk).exists()


class TestProductAnalytics:
    def test_create(self):
        analytics = ProductAnalyticsFactory()
        assert analytics.pk is not None
        assert analytics.product is not None
        assert analytics.units_sold >= 0

    def test_str(self):
        analytics = ProductAnalyticsFactory()
        assert analytics.product.name in str(analytics)

    def test_product_cascade_delete(self):
        analytics = ProductAnalyticsFactory()
        product = analytics.product
        product.delete()
        assert not ProductAnalytics.objects.filter(pk=analytics.pk).exists()

    def test_views_default_zero(self):
        analytics = ProductAnalyticsFactory(views=0)
        assert analytics.views == 0


class TestPerformanceMetric:
    def test_create(self):
        metric = PerformanceMetricFactory()
        assert metric.pk is not None
        assert metric.metric_type == MetricType.REVENUE
        assert metric.value >= 0

    def test_str(self):
        metric = PerformanceMetricFactory(value=Decimal("12345.6789"))
        assert "12345" in str(metric)

    def test_change_percentage_nullable(self):
        metric = PerformanceMetricFactory(change_percentage=None, previous_value=None)
        assert metric.change_percentage is None
        assert metric.previous_value is None

    def test_all_metric_types(self):
        for metric_type in MetricType:
            m = PerformanceMetricFactory(metric_type=metric_type)
            assert m.metric_type == metric_type
