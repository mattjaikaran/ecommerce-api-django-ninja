from django.contrib import admin
from unfold.admin import ModelAdmin

from orders.models import IdempotencyKey


@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(ModelAdmin):
    list_display = (
        "id",
        "key_hash",
        "user",
        "order",
        "expires_at",
        "created_at",
    )
    list_filter = ("expires_at", "created_at")
    search_fields = ("key_hash", "user__email", "order__order_number")
    readonly_fields = ("id", "key_hash", "request_hash", "user", "order", "expires_at", "created_at", "updated_at")
    ordering = ("-created_at",)
