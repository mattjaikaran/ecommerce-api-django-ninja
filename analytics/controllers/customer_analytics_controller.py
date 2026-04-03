import logging

from ninja.pagination import paginate
from ninja_extra import (
    api_controller,
    http_get,
)
from ninja_extra.permissions import IsAuthenticated

from api.decorators import handle_exceptions, log_api_call

from ..models import CustomerAnalytics
from ..schemas import CustomerAnalyticsSchema

logger = logging.getLogger(__name__)


@api_controller("/analytics/customers", tags=["Analytics - Customers"])
class CustomerAnalyticsController:
    permission_classes = [IsAuthenticated]

    @http_get("", response={200: list[CustomerAnalyticsSchema]})
    @handle_exceptions
    @log_api_call()
    @paginate
    def list_customer_analytics(self, request, period: str | None = None):
        """Get paginated list of customer analytics."""
        qs = CustomerAnalytics.objects.select_related("customer").order_by(
            "-period_start"
        )
        if period:
            qs = qs.filter(period=period)
        return qs

    @http_get("/{customer_id}", response={200: list[CustomerAnalyticsSchema]})
    @handle_exceptions
    @log_api_call()
    def get_customer_analytics(self, request, customer_id: str):
        """Get analytics for a specific customer."""
        analytics = (
            CustomerAnalytics.objects.filter(customer_id=customer_id)
            .select_related("customer")
            .order_by("-period_start")
        )
        return 200, list(analytics)
