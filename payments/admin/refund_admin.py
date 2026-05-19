from django.contrib import admin
from unfold.admin import ModelAdmin

from ..models import PaymentRefund


@admin.register(PaymentRefund)
class PaymentRefundAdmin(ModelAdmin):
    list_display = ("id", "transaction", "amount", "currency", "status", "reason", "created_at")
    list_filter = ("status", "reason", "created_at")
    search_fields = ("transaction__stripe_payment_intent_id", "stripe_refund_id", "notes")
    readonly_fields = ("id", "created_at", "updated_at", "gateway_response", "stripe_refund_id")
    ordering = ("-created_at",)
