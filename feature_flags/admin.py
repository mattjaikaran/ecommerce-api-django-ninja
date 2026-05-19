from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import FeatureFlag


@admin.register(FeatureFlag)
class FeatureFlagAdmin(ModelAdmin):
    list_display = ("name", "is_enabled", "rollout_percentage", "created_at")
    list_filter = ("is_enabled",)
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")
