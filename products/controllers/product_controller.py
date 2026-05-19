"""Product management controller with modern decorator-based approach."""

import logging
from uuid import UUID

from django.db import models, transaction
from django.shortcuts import get_object_or_404
from ninja_extra import api_controller, http_delete, http_get, http_post, http_put

from api.decorators import (
    admin_endpoint,
    create_endpoint,
    delete_endpoint,
    detail_endpoint,
    list_endpoint,
    search_and_filter,
    update_endpoint,
)
from products.models import (
    Product,
    ProductVariant,
)
from products.schemas import (
    ProductCreateSchema,
    ProductListSchema,
    ProductSchema,
    ProductUpdateSchema,
    ProductVariantCreateSchema,
    ProductVariantSchema,
    ProductVariantUpdateSchema,
)

logger = logging.getLogger(__name__)


@api_controller("/products", tags=["Products"])
class ProductController:
    """Product management controller with comprehensive decorators."""

    @http_get("", response={200: list[ProductListSchema], 400: dict, 401: dict, 403: dict})
    @list_endpoint(
        cache_timeout=300,
        select_related=["category", "created_by", "updated_by"],
        prefetch_related=[
            "variants",
            "tags",
            "collections",
            "images",
            "attributes",
            "reviews",
        ],
        search_fields=["name", "description", "slug"],
        filter_fields={
            "category_id": "exact",
            "status": "exact",
            "is_active": "boolean",
            "featured": "boolean",
            "type": "exact",
        },
        ordering_fields=[
            "name",
            "price",
            "created_at",
            "updated_at",
            "featured",
            "quantity",
        ],
    )
    @search_and_filter(
        search_fields=["name", "description", "slug"],
        filter_fields={
            "category_id": "exact",
            "status": "exact",
            "is_active": "boolean",
            "featured": "boolean",
            "type": "exact",
        },
        ordering_fields=["name", "price", "created_at", "featured"],
    )
    def list_products(self, request):
        """Get all products with advanced filtering and optimization."""
        return 200, Product.objects.filter(is_active=True)

    @http_get("/{product_id}", response={200: ProductSchema, 400: dict, 401: dict, 403: dict, 404: dict})
    @detail_endpoint(
        cache_timeout=600,
        select_related=["category", "created_by", "updated_by"],
        prefetch_related=[
            "variants__options__option",
            "variants__options__value",
            "tags",
            "collections",
            "images",
            "attributes__attribute",
            "reviews__customer__user",
            "bundles__bundle_items__product",
        ],
    )
    def get_product(self, request, product_id: UUID):
        """Get a specific product by ID with complete related data."""
        product = get_object_or_404(Product, id=product_id, is_active=True)
        return 200, ProductSchema.from_orm(product)

    @http_post("", response={201: ProductSchema, 400: dict, 401: dict, 403: dict, 409: dict, 500: dict})
    @create_endpoint(require_admin=True)
    @transaction.atomic
    def create_product(self, request, payload: ProductCreateSchema):
        """Create a new product."""
        product = Product.objects.create(
            **payload.dict(),
            created_by=request.user,
            updated_by=request.user,
        )
        return 201, ProductSchema.from_orm(product)

    @http_put("/{product_id}", response={200: ProductSchema, 400: dict, 401: dict, 403: dict, 404: dict, 409: dict, 422: dict})
    @update_endpoint(require_admin=True)
    @transaction.atomic
    def update_product(self, request, product_id: UUID, payload: ProductUpdateSchema):
        """Update a product."""
        product = get_object_or_404(Product, id=product_id)

        for field, value in payload.dict(exclude_unset=True).items():
            setattr(product, field, value)

        product.updated_by = request.user
        product.save()

        return 200, ProductSchema.from_orm(product)

    @http_delete("/{product_id}", response={204: None, 401: dict, 403: dict, 404: dict})
    @delete_endpoint(require_admin=True)
    def delete_product(self, request, product_id: UUID):
        """Soft delete a product."""
        product = get_object_or_404(Product, id=product_id)
        product.is_active = False
        product.is_deleted = True
        product.deleted_by = request.user
        product.save()
        return 204, None

    @http_get("/{product_id}/variants", response={200: list[ProductVariantSchema]})
    @list_endpoint(
        cache_timeout=300,
        select_related=["product"],
        prefetch_related=["options__option", "options__value"],
        filter_fields={"is_active": "boolean"},
        ordering_fields=["position", "name", "price"],
    )
    def get_product_variants(self, request, product_id: UUID):
        """Get all variants for a product."""
        product = get_object_or_404(Product, id=product_id, is_active=True)
        return 200, product.variants.filter(is_active=True).order_by("position")

    @http_post(
        "/{product_id}/variants", response={201: ProductVariantSchema, 400: dict}
    )
    @create_endpoint(require_admin=True)
    @transaction.atomic
    def create_product_variant(
        self, request, product_id: UUID, payload: ProductVariantCreateSchema
    ):
        """Create a new product variant."""
        product = get_object_or_404(Product, id=product_id)

        variant = ProductVariant.objects.create(
            product=product,
            **payload.dict(),
            created_by=request.user,
            updated_by=request.user,
        )

        return 201, ProductVariantSchema.from_orm(variant)

    @http_put(
        "/{product_id}/variants/{variant_id}",
        response={200: ProductVariantSchema, 400: dict, 404: dict},
    )
    @update_endpoint(require_admin=True)
    @transaction.atomic
    def update_product_variant(
        self,
        request,
        product_id: UUID,
        variant_id: UUID,
        payload: ProductVariantUpdateSchema,
    ):
        """Update a product variant."""
        product = get_object_or_404(Product, id=product_id)
        variant = get_object_or_404(ProductVariant, id=variant_id, product=product)

        for field, value in payload.dict(exclude_unset=True).items():
            setattr(variant, field, value)

        variant.updated_by = request.user
        variant.save()

        return 200, ProductVariantSchema.from_orm(variant)

    @http_delete(
        "/{product_id}/variants/{variant_id}",
        response={204: None, 404: dict},
    )
    @delete_endpoint(require_admin=True)
    def delete_product_variant(self, request, product_id: UUID, variant_id: UUID):
        """Soft delete a product variant."""
        product = get_object_or_404(Product, id=product_id)
        variant = get_object_or_404(ProductVariant, id=variant_id, product=product)

        variant.is_active = False
        variant.is_deleted = True
        variant.deleted_by = request.user
        variant.save()

        return 204, None

    @http_get("/search", response={200: list[ProductListSchema]})
    @list_endpoint(
        cache_timeout=180,
        select_related=["category"],
        prefetch_related=["variants", "tags", "images"],
        search_fields=["name", "description", "slug", "category__name"],
        filter_fields={
            "category_id": "exact",
            "status": "exact",
            "featured": "boolean",
            "price_min": "gte",
            "price_max": "lte",
        },
        ordering_fields=["name", "price", "created_at", "featured"],
    )
    @search_and_filter(
        search_fields=["name", "description", "slug", "category__name"],
        filter_fields={
            "category_id": "exact",
            "status": "exact",
            "featured": "boolean",
        },
        ordering_fields=["name", "price", "created_at", "featured"],
    )
    def search_products(self, request):
        """Advanced product search with comprehensive filtering."""
        return 200, Product.objects.filter(is_active=True, status="published")

    @http_get("/featured", response={200: list[ProductListSchema]})
    @list_endpoint(
        cache_timeout=600,
        select_related=["category"],
        prefetch_related=["variants", "images", "tags"],
        ordering_fields=["created_at", "name", "price"],
    )
    def get_featured_products(self, request):
        """Get featured products."""
        return 200, Product.objects.filter(
            is_active=True, featured=True, status="published"
        ).order_by("-created_at")

    @http_get("/categories/{category_id}", response={200: list[ProductListSchema]})
    @list_endpoint(
        cache_timeout=300,
        select_related=["category"],
        prefetch_related=["variants", "images"],
        filter_fields={
            "status": "exact",
            "featured": "boolean",
        },
        ordering_fields=["name", "price", "created_at"],
    )
    @search_and_filter(
        filter_fields={
            "status": "exact",
            "featured": "boolean",
        },
        ordering_fields=["name", "price", "created_at"],
    )
    def get_products_by_category(self, request, category_id: UUID):
        """Get products by category."""
        return 200, Product.objects.filter(
            category_id=category_id, is_active=True, status="published"
        )

    @http_get("/low-stock", response={200: list[ProductListSchema]})
    @admin_endpoint(
        cache_timeout=60,
        select_related=["category"],
        prefetch_related=["variants"],
        ordering_fields=["quantity", "name"],
    )
    def get_low_stock_products(self, request):
        """Get products with low stock levels."""
        return 200, Product.objects.filter(
            is_active=True, quantity__lte=models.F("low_stock_threshold")
        ).order_by("quantity")
