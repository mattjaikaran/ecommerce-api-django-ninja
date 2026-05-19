from django.contrib import admin
from unfold.admin import ModelAdmin

from ..models import StripeWebhookEvent


@admin.register(StripeWebhookEvent)
class StripeWebhookEventAdmin(ModelAdmin):
    list_display = ("stripe_event_id", "event_type", "status", "received_at", "processed_at")
    list_filter = ("status", "event_type", "received_at")
    search_fields = ("stripe_event_id", "event_type", "error")
    readonly_fields = ("id", "stripe_event_id", "event_type", "payload", "received_at", "processed_at", "error")
    ordering = ("-received_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
