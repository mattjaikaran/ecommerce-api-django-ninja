from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Coupon, CouponUsage


class CouponUsageInline(TabularInline):
    model = CouponUsage
    extra = 0
    readonly_fields = ("customer", "order", "discount_applied", "created_at")
    can_delete = False


@admin.register(Coupon)
class CouponAdmin(ModelAdmin):
    list_display = (
        "code", "discount_type", "discount_value", "used_count",
        "usage_limit", "valid_from", "valid_to", "is_active",
    )
    list_filter = ("discount_type", "is_active")
    search_fields = ("code", "description")
    readonly_fields = ("used_count", "created_at", "updated_at")
    inlines = [CouponUsageInline]


@admin.register(CouponUsage)
class CouponUsageAdmin(ModelAdmin):
    list_display = ("coupon", "customer", "order", "discount_applied", "created_at")
    list_filter = ("coupon",)
    search_fields = ("coupon__code", "customer__email")
    readonly_fields = ("created_at", "updated_at")
