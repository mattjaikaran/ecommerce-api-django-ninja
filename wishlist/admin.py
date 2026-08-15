from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Wishlist, WishlistItem


class WishlistItemInline(TabularInline):
    model = WishlistItem
    extra = 0
    readonly_fields = (
        "product_variant",
        "quantity",
        "notes",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )


@admin.register(Wishlist)
class WishlistAdmin(ModelAdmin):
    list_display = ("customer", "name", "created_at", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("customer__user__email", "customer__user__username", "name")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    inlines = [WishlistItemInline]


@admin.register(WishlistItem)
class WishlistItemAdmin(ModelAdmin):
    list_display = ("wishlist", "product_variant", "quantity", "created_at")
    list_filter = ("wishlist",)
    search_fields = ("product_variant__name", "product_variant__sku")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
