"""Customer management controller with modern decorator-based approach."""

import logging
from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja_extra import api_controller, http_delete, http_get, http_post, http_put

from api.decorators import (
    create_endpoint,
    delete_endpoint,
    detail_endpoint,
    list_endpoint,
    search_and_filter,
    update_endpoint,
)
from core.models import Customer
from core.schemas.customer_schema import (
    CustomerCreateSchema,
    CustomerSchema,
    CustomerUpdateSchema,
)

logger = logging.getLogger(__name__)


@api_controller("/customers", tags=["Customers"])
class CustomerController:
    """Customer management controller with comprehensive decorators."""

    @http_get("", response={200: list[CustomerSchema]})
    @list_endpoint(
        select_related=["user"],
        prefetch_related=["orders", "customer_groups"],
        search_fields=[
            "user__username",
            "user__email",
            "user__first_name",
            "user__last_name",
            "phone",
        ],
        filter_fields={
            "is_default": "boolean",
            "is_active": "boolean",
        },
        ordering_fields=["created_at", "user__username", "user__email"],
    )
    @search_and_filter(
        search_fields=[
            "user__username",
            "user__email",
            "user__first_name",
            "user__last_name",
            "phone",
        ],
        filter_fields={
            "is_default": "boolean",
            "is_active": "boolean",
        },
        ordering_fields=["created_at", "user__username"],
    )
    def list_customers(self, request):
        """Get all customers with advanced filtering and search."""
        return 200, Customer.objects.filter(is_active=True)

    @http_get("/{customer_id}", response={200: CustomerSchema, 404: dict})
    @detail_endpoint(
        select_related=["user"],
        prefetch_related=[
            "orders__items__product_variant__product",
            "customer_groups",
            "user__addresses",
        ],
    )
    def get_customer(self, request, customer_id: UUID):
        """Get a customer by ID with related data."""
        customer = get_object_or_404(Customer, id=customer_id, is_active=True)
        return 200, CustomerSchema.from_orm(customer)

    @http_post("", response={201: CustomerSchema, 400: dict})
    @create_endpoint()
    def create_customer(self, request, payload: CustomerCreateSchema):
        """Create a new customer."""
        customer = Customer.objects.create(
            **payload.dict(),
            created_by=request.user,
            updated_by=request.user,
        )
        return 201, CustomerSchema.from_orm(customer)

    @http_put("/{customer_id}", response={200: CustomerSchema, 400: dict, 404: dict})
    @update_endpoint()
    def update_customer(
        self, request, customer_id: UUID, payload: CustomerUpdateSchema
    ):
        """Update a customer's information."""
        customer = get_object_or_404(Customer, id=customer_id)

        for field, value in payload.dict(exclude_unset=True).items():
            setattr(customer, field, value)

        customer.updated_by = request.user
        customer.save()

        return 200, CustomerSchema.from_orm(customer)

    @http_delete("/{customer_id}", response={204: None, 404: dict})
    @delete_endpoint()
    def delete_customer(self, request, customer_id: UUID):
        """Soft delete a customer."""
        customer = get_object_or_404(Customer, id=customer_id)
        customer.is_active = False
        customer.is_deleted = True
        customer.deleted_by = request.user
        customer.save()
        return 204, None

    @http_get("/{customer_id}/orders", response={200: list})
    @list_endpoint(
        select_related=["billing_address", "shipping_address"],
        prefetch_related=["items__product_variant__product"],
        filter_fields={
            "status": "exact",
            "payment_status": "exact",
        },
        ordering_fields=["created_at", "order_number", "total"],
    )
    def get_customer_orders(self, request, customer_id: UUID):
        """Get all orders for a specific customer."""
        customer = get_object_or_404(Customer, id=customer_id)
        return 200, customer.orders.all().order_by("-created_at")

    @http_get("/search", response={200: list[CustomerSchema]})
    @list_endpoint(
        cache_timeout=300,
        select_related=["user"],
        search_fields=[
            "user__username",
            "user__email",
            "user__first_name",
            "user__last_name",
            "phone",
        ],
        filter_fields={
            "is_default": "boolean",
            "is_active": "boolean",
            "has_orders": "boolean",
        },
        ordering_fields=["created_at", "user__username", "user__email"],
    )
    @search_and_filter(
        search_fields=[
            "user__username",
            "user__email",
            "user__first_name",
            "user__last_name",
            "phone",
        ],
        filter_fields={
            "is_default": "boolean",
            "is_active": "boolean",
        },
        ordering_fields=["created_at", "user__username"],
    )
    def search_customers(self, request):
        """Advanced customer search with filtering."""
        return 200, Customer.objects.filter(is_active=True)

    @http_get("/stats", response={200: dict})
    @detail_endpoint(cache_timeout=600)
    def get_customer_stats(self, request):
        """Get customer statistics."""
        from django.db.models import Count, Sum

        stats = Customer.objects.filter(is_active=True).aggregate(
            total_customers=Count("id"),
            customers_with_orders=Count("orders", distinct=True),
            total_order_value=Sum("orders__total"),
        )

        return 200, stats
