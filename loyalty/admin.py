from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import LoyaltyAccount, LoyaltyTransaction


@admin.register(LoyaltyAccount)
class LoyaltyAccountAdmin(ModelAdmin):
    list_display = (
        "customer",
        "balance",
        "lifetime_points",
        "is_active",
        "created_at",
    )
    search_fields = ("customer__user__email", "customer__user__username")
    readonly_fields = (
        "balance",
        "lifetime_points",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
    )


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(ModelAdmin):
    list_display = ("account", "amount", "reason", "order", "reference", "created_at")
    list_filter = ("reason",)
    search_fields = ("reference", "account__customer__user__email")
    readonly_fields = (
        "account",
        "amount",
        "order",
        "reason",
        "reference",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
    )
