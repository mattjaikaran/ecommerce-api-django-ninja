from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import CustomerSubscription, SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(ModelAdmin):
    list_display = ("name", "interval", "amount", "currency", "is_active", "created_at")
    list_filter = ("interval", "is_active")
    search_fields = ("name", "stripe_price_id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(CustomerSubscription)
class CustomerSubscriptionAdmin(ModelAdmin):
    list_display = ("customer", "plan", "status", "cancel_at_period_end", "current_period_end", "created_at")
    list_filter = ("status", "cancel_at_period_end")
    search_fields = ("stripe_subscription_id", "stripe_customer_id")
    readonly_fields = ("created_at", "updated_at")
