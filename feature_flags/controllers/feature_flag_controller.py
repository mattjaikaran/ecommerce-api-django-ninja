from datetime import datetime
from uuid import UUID

from ninja import Schema
from ninja.pagination import paginate
from ninja_extra import api_controller, http_get
from ninja_extra.permissions import IsAuthenticated

from feature_flags.models import FeatureFlag
from feature_flags.services import is_flag_enabled


class FeatureFlagSchema(Schema):
    id: UUID
    name: str
    description: str | None = None
    is_enabled: bool
    rollout_percentage: int
    created_at: datetime
    updated_at: datetime


class FlagCheckSchema(Schema):
    enabled: bool


@api_controller("/feature-flags", tags=["Feature Flags"])
class FeatureFlagController:
    permission_classes = [IsAuthenticated]

    @http_get("", response={200: list[FeatureFlagSchema]})
    @paginate
    def list_flags(self, request):
        return FeatureFlag.objects.all()

    @http_get("/{name}", response={200: FeatureFlagSchema})
    def get_flag(self, request, name: str):
        from django.shortcuts import get_object_or_404

        flag = get_object_or_404(FeatureFlag, name=name)
        return 200, flag

    @http_get("/{name}/check", response={200: FlagCheckSchema})
    def check_flag(self, request, name: str):
        enabled = is_flag_enabled(name, user=request.user)
        return 200, FlagCheckSchema(enabled=enabled)
