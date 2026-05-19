"""Seed analytics data: sales reports, customer analytics, product analytics, performance metrics."""

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from analytics.models import CustomerAnalytics, PerformanceMetric, ProductAnalytics, SalesReport
from analytics.models.choices import MetricType, ReportType, TimePeriod
from core.models import Customer
from products.models import Product

User = get_user_model()


class Command(BaseCommand):
    help = "Generate sample analytics data"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30, help="Number of days of daily reports")
        parser.add_argument("--clear", action="store_true", help="Delete existing analytics data first")

    def handle(self, *args, **options):
        days = options["days"]
        clear = options["clear"]

        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stdout.write(self.style.ERROR("No superuser found. Run create_superuser first."))
            return

        if clear:
            SalesReport.objects.all().delete()
            CustomerAnalytics.objects.all().delete()
            ProductAnalytics.objects.all().delete()
            PerformanceMetric.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing analytics data."))

        now = timezone.now()

        # Sales reports — daily for `days` days
        sales_created = 0
        for i in range(days):
            period_start = (now - timedelta(days=days - i)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            period_end = period_start + timedelta(days=1)
            revenue = Decimal(str(round(random.uniform(500, 15000), 2)))
            orders = random.randint(5, 150)
            refunds = Decimal(str(round(random.uniform(0, float(revenue) * 0.05), 2)))
            SalesReport.objects.get_or_create(
                period=TimePeriod.DAILY,
                period_start=period_start,
                defaults=dict(
                    report_type=ReportType.SALES,
                    period_end=period_end,
                    total_revenue=revenue,
                    total_orders=orders,
                    total_items_sold=orders * random.randint(1, 4),
                    average_order_value=revenue / orders,
                    total_discounts=Decimal(str(round(random.uniform(0, float(revenue) * 0.1), 2))),
                    total_refunds=refunds,
                    total_tax=Decimal(str(round(float(revenue) * 0.08, 2))),
                    total_shipping=Decimal(str(round(random.uniform(0, orders * 10), 2))),
                    net_revenue=revenue - refunds,
                    new_customers=random.randint(0, 20),
                    returning_customers=random.randint(0, orders),
                    created_by=admin,
                    updated_by=admin,
                ),
            )
            sales_created += 1
        self.stdout.write(f"  Sales reports: {sales_created}")

        # Customer analytics — one entry per customer
        customers = list(Customer.objects.all()[:50])
        cust_created = 0
        for customer in customers:
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            period_end = (
                period_start.replace(month=period_start.month % 12 + 1)
                if period_start.month < 12
                else period_start.replace(year=period_start.year + 1, month=1)
            )
            total_orders = random.randint(1, 15)
            total_spent = Decimal(str(round(random.uniform(50, 2000), 2)))
            _, created = CustomerAnalytics.objects.get_or_create(
                customer=customer,
                period=TimePeriod.MONTHLY,
                period_start=period_start,
                defaults=dict(
                    period_end=period_end,
                    total_orders=total_orders,
                    total_spent=total_spent,
                    average_order_value=total_spent / total_orders,
                    total_returns=random.randint(0, 2),
                    lifetime_value=total_spent,
                    created_by=admin,
                    updated_by=admin,
                ),
            )
            if created:
                cust_created += 1
        self.stdout.write(f"  Customer analytics: {cust_created}")

        # Product analytics — one entry per product for today
        products = list(Product.objects.filter(is_active=True)[:50])
        prod_created = 0
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=1)
        for product in products:
            units = random.randint(0, 30)
            views = random.randint(10, 500)
            revenue = Decimal(str(round(units * float(product.price), 2)))
            _, created = ProductAnalytics.objects.get_or_create(
                product=product,
                period=TimePeriod.DAILY,
                period_start=period_start,
                defaults=dict(
                    period_end=period_end,
                    units_sold=units,
                    revenue=revenue,
                    views=views,
                    conversion_rate=Decimal(str(round(units / views * 100, 2))) if views else Decimal("0.00"),
                    returns=random.randint(0, max(1, units // 10)),
                    created_by=admin,
                    updated_by=admin,
                ),
            )
            if created:
                prod_created += 1
        self.stdout.write(f"  Product analytics: {prod_created}")

        # Performance metrics — one entry per metric type for today
        metric_created = 0
        for metric_type in MetricType:
            value = Decimal(str(round(random.uniform(100, 10000), 4)))
            previous = Decimal(str(round(random.uniform(100, 10000), 4)))
            change = ((value - previous) / previous * 100).quantize(Decimal("0.01")) if previous else None
            _, created = PerformanceMetric.objects.get_or_create(
                metric_type=metric_type,
                period=TimePeriod.DAILY,
                period_start=period_start,
                defaults=dict(
                    period_end=period_end,
                    value=value,
                    previous_value=previous,
                    change_percentage=change,
                    created_by=admin,
                    updated_by=admin,
                ),
            )
            if created:
                metric_created += 1
        self.stdout.write(f"  Performance metrics: {metric_created}")

        self.stdout.write(self.style.SUCCESS("Analytics seed complete."))
