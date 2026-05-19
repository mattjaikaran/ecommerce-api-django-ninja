from django.shortcuts import get_object_or_404
from ninja.pagination import paginate
from ninja_extra import api_controller, http_delete, http_get, http_post, http_put
from ninja_extra.permissions import IsAuthenticated

from outbound_webhooks.models import WebhookDelivery, WebhookEndpoint
from outbound_webhooks.schemas import (
    WebhookDeliverySchema,
    WebhookEndpointCreateSchema,
    WebhookEndpointSchema,
    WebhookEndpointUpdateSchema,
)
from outbound_webhooks.services import WebhookService


@api_controller("/webhook-endpoints", tags=["Webhooks"])
class WebhookEndpointController:
    permission_classes = [IsAuthenticated]

    @http_get("", response={200: list[WebhookEndpointSchema]})
    @paginate
    def list_endpoints(self, request):
        return WebhookEndpoint.objects.all()

    @http_post("", response={201: WebhookEndpointSchema})
    def create_endpoint(self, request, payload: WebhookEndpointCreateSchema):
        endpoint = WebhookService.create_endpoint(payload)
        return 201, endpoint

    @http_get("/{endpoint_id}", response={200: WebhookEndpointSchema})
    def get_endpoint(self, request, endpoint_id: str):
        endpoint = get_object_or_404(WebhookEndpoint, id=endpoint_id)
        return 200, endpoint

    @http_put("/{endpoint_id}", response={200: WebhookEndpointSchema})
    def update_endpoint(self, request, endpoint_id: str, payload: WebhookEndpointUpdateSchema):
        endpoint = get_object_or_404(WebhookEndpoint, id=endpoint_id)
        endpoint = WebhookService.update_endpoint(endpoint, payload)
        return 200, endpoint

    @http_delete("/{endpoint_id}", response={204: None})
    def delete_endpoint(self, request, endpoint_id: str):
        endpoint = get_object_or_404(WebhookEndpoint, id=endpoint_id)
        WebhookService.delete_endpoint(endpoint)
        return 204, None

    @http_get("/{endpoint_id}/deliveries", response={200: list[WebhookDeliverySchema]})
    @paginate
    def list_deliveries(self, request, endpoint_id: str):
        get_object_or_404(WebhookEndpoint, id=endpoint_id)
        return WebhookService.list_deliveries(endpoint_id)


@api_controller("/webhook-deliveries", tags=["Webhooks"])
class WebhookDeliveryController:
    permission_classes = [IsAuthenticated]

    @http_get("/{delivery_id}", response={200: WebhookDeliverySchema})
    def get_delivery(self, request, delivery_id: str):
        delivery = get_object_or_404(WebhookDelivery, id=delivery_id)
        return 200, delivery

    @http_post("/{delivery_id}/redeliver", response={200: WebhookDeliverySchema})
    def redeliver(self, request, delivery_id: str):
        delivery = WebhookService.redeliver(delivery_id)
        return 200, delivery
