import logging

from ninja.pagination import paginate
from ninja_extra import (
    api_controller,
    http_get,
)
from ninja_extra.permissions import IsAuthenticated

from api.decorators import handle_exceptions, log_api_call

from ..models import ProductAnalytics
from ..schemas import ProductAnalyticsSchema

logger = logging.getLogger(__name__)


@api_controller("/analytics/products", tags=["Analytics - Products"])
class ProductAnalyticsController:
    permission_classes = [IsAuthenticated]

    @http_get("", response={200: list[ProductAnalyticsSchema]})
    @handle_exceptions
    @log_api_call()
    @paginate
    def list_product_analytics(self, request, period: str | None = None):
        """Get paginated list of product analytics."""
        qs = ProductAnalytics.objects.select_related("product").order_by(
            "-period_start"
        )
        if period:
            qs = qs.filter(period=period)
        return qs

    @http_get("/{product_id}", response={200: list[ProductAnalyticsSchema]})
    @handle_exceptions
    @log_api_call()
    def get_product_analytics(self, request, product_id: str):
        """Get analytics for a specific product."""
        analytics = (
            ProductAnalytics.objects.filter(product_id=product_id)
            .select_related("product")
            .order_by("-period_start")
        )
        return 200, list(analytics)
