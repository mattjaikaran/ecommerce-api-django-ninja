from django.contrib import admin
from unfold.admin import ModelAdmin

from ..models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(ModelAdmin):
    list_display = ("id", "order", "payment_method", "gateway", "status", "amount", "currency", "created_at")
    list_filter = ("status", "gateway", "currency", "created_at")
    search_fields = ("order__order_number", "stripe_payment_intent_id", "stripe_charge_id")
    readonly_fields = ("id", "created_at", "updated_at", "gateway_response")
    ordering = ("-created_at",)
    fieldsets = (
        ("Transaction", {"fields": ("order", "payment_method", "gateway", "status")}),
        ("Financials", {"fields": ("amount", "currency", "fee")}),
        ("Stripe", {"fields": ("stripe_payment_intent_id", "stripe_charge_id")}),
        ("Error", {"fields": ("error_code", "error_message"), "classes": ("collapse",)}),
        ("Raw Response", {"fields": ("gateway_response",), "classes": ("collapse",)}),
        ("Metadata", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )
