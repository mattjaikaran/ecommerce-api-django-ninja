from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import GiftCard, GiftCardTransaction


@admin.register(GiftCard)
class GiftCardAdmin(ModelAdmin):
    list_display = ("code", "initial_balance", "current_balance", "is_active", "issued_to", "expires_at", "created_at")
    list_filter = ("is_active",)
    search_fields = ("code",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(GiftCardTransaction)
class GiftCardTransactionAdmin(ModelAdmin):
    list_display = ("gift_card", "amount", "transaction_type", "order_id", "created_at")
    list_filter = ("transaction_type",)
    readonly_fields = ("created_at",)
