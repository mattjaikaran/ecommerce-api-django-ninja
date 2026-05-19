from django.contrib import admin
from unfold.admin import ModelAdmin

from ..models import PaymentMethod


@admin.register(PaymentMethod)
class PaymentMethodAdmin(ModelAdmin):
    list_display = ("id", "customer", "type", "provider", "card_brand", "last_four", "is_default", "is_active", "created_at")
    list_filter = ("provider", "type", "is_default", "is_active", "created_at")
    search_fields = ("customer__user__email", "stripe_payment_method_id", "stripe_customer_id", "last_four")
    readonly_fields = ("id", "created_at", "updated_at", "stripe_payment_method_id", "stripe_customer_id")
    ordering = ("-created_at",)
    fieldsets = (
        ("Customer", {"fields": ("customer", "is_default", "is_active")}),
        ("Card Details", {"fields": ("type", "provider", "last_four", "card_brand", "expiry_month", "expiry_year")}),
        ("Stripe IDs", {"fields": ("stripe_payment_method_id", "stripe_customer_id"), "classes": ("collapse",)}),
        ("Metadata", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )
