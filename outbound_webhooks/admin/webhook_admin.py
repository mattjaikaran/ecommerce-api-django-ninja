from django.contrib import admin
from unfold.admin import ModelAdmin

from outbound_webhooks.models import WebhookDelivery, WebhookEndpoint


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(ModelAdmin):
    list_display = ("url", "is_active", "failure_count", "last_success_at", "created_at")
    list_filter = ("is_active",)
    search_fields = ("url", "description")
    readonly_fields = ("created_at", "updated_at", "failure_count", "last_success_at")


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(ModelAdmin):
    list_display = ("event_type", "endpoint", "status", "attempt_count", "delivered_at", "created_at")
    list_filter = ("status", "event_type")
    search_fields = ("event_type", "endpoint__url")
    readonly_fields = ("created_at", "updated_at", "delivered_at")
