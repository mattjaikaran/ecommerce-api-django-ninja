from django.contrib import admin
from unfold.admin import ModelAdmin

from ..models import (
    CustomerAnalytics,
    PerformanceMetric,
    ProductAnalytics,
    SalesReport,
)


@admin.register(SalesReport)
class SalesReportAdmin(ModelAdmin):
    list_display = (
        "id",
        "report_type",
        "period",
        "period_start",
        "total_revenue",
        "total_orders",
    )
    list_filter = ("report_type", "period")
    search_fields = ("id",)
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-period_start",)


@admin.register(PerformanceMetric)
class PerformanceMetricAdmin(ModelAdmin):
    list_display = (
        "id",
        "metric_type",
        "period",
        "period_start",
        "value",
        "change_percentage",
    )
    list_filter = ("metric_type", "period")
    search_fields = ("id",)
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-period_start",)


@admin.register(ProductAnalytics)
class ProductAnalyticsAdmin(ModelAdmin):
    list_display = ("id", "product", "period", "period_start", "units_sold", "revenue")
    list_filter = ("period",)
    search_fields = ("product__name",)
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-period_start",)


@admin.register(CustomerAnalytics)
class CustomerAnalyticsAdmin(ModelAdmin):
    list_display = (
        "id",
        "customer",
        "period",
        "period_start",
        "total_orders",
        "total_spent",
    )
    list_filter = ("period",)
    search_fields = ("customer__id",)
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-period_start",)
