import logging
from uuid import UUID

from django.db import transaction
from django.shortcuts import get_object_or_404
from ninja.pagination import paginate
from ninja_extra import api_controller, http_delete, http_get, http_post, http_put
from ninja_extra.permissions import IsAuthenticated

from api.decorators import handle_exceptions, log_api_call

from ..models import BundleItem, Product, ProductBundle
from ..schemas.bundle_schema import (
    BundleCreateSchema,
    BundleItemCreateSchema,
    BundleItemSchema,
    BundleItemUpdateSchema,
    BundleSchema,
    BundleUpdateSchema,
)

logger = logging.getLogger(__name__)


@api_controller("/products/bundles", tags=["Product Bundles"])
class BundleController:
    permission_classes = [IsAuthenticated]

    @http_get("", response={200: list[BundleSchema]})
    @handle_exceptions
    @log_api_call()
    @paginate
    def list_bundles(self, request):
        """Get paginated list of bundles."""
        bundles = ProductBundle.objects.prefetch_related("items__product").order_by(
            "-created_at"
        )
        return 200, bundles

    @http_get("/{id}", response={200: BundleSchema})
    @handle_exceptions
    @log_api_call()
    def get_bundle(self, request, id: UUID):
        """Get bundle by ID."""
        bundle = get_object_or_404(
            ProductBundle.objects.prefetch_related("items__product"), id=id
        )
        return 200, bundle

    @http_post("", response={201: BundleSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def create_bundle(self, request, data: BundleCreateSchema):
        """Create new product bundle."""
        bundle = ProductBundle.objects.create(
            name=data.name,
            slug=data.slug,
            description=data.description,
            discount_percentage=data.discount_percentage,
            is_active=data.is_active,
            start_date=data.start_date,
            end_date=data.end_date,
        )

        for item in data.items:
            product = get_object_or_404(Product, id=item.product_id)
            BundleItem.objects.create(
                bundle=bundle,
                product=product,
                quantity=item.quantity,
                position=item.position,
            )

        return 201, bundle

    @http_put("/{bundle_id}", response={200: BundleSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def update_bundle(self, request, bundle_id: UUID, data: BundleUpdateSchema):
        """Update product bundle."""
        bundle = get_object_or_404(ProductBundle, id=bundle_id)

        for field, value in data.dict(exclude_unset=True, exclude={"items"}).items():
            setattr(bundle, field, value)
        bundle.save()

        if data.items is not None:
            # Remove existing items
            bundle.items.all().delete()

            # Add new items
            for item in data.items:
                product = get_object_or_404(Product, id=item.product_id)
                BundleItem.objects.create(
                    bundle=bundle,
                    product=product,
                    quantity=item.quantity,
                    position=item.position,
                )

        return 200, bundle

    @http_delete("/{bundle_id}", response={204: None})
    @handle_exceptions
    @log_api_call()
    def delete_bundle(self, request, bundle_id: UUID):
        """Delete product bundle."""
        bundle = get_object_or_404(ProductBundle, id=bundle_id)
        bundle.delete()
        return 204, None

    @http_get("/{bundle_id}/items", response={200: list[BundleItemSchema]})
    @handle_exceptions
    @log_api_call()
    @paginate
    def list_bundle_items(self, request, bundle_id: UUID):
        """List all items in a bundle."""
        items = (
            BundleItem.objects.filter(bundle_id=bundle_id)
            .select_related("product")
            .order_by("position")
        )
        return 200, items

    @http_post("/{bundle_id}/items", response={201: BundleItemSchema})
    @handle_exceptions
    @log_api_call()
    def add_bundle_item(self, request, bundle_id: UUID, data: BundleItemCreateSchema):
        """Add item to a bundle."""
        bundle = get_object_or_404(ProductBundle, id=bundle_id)
        product = get_object_or_404(Product, id=data.product_id)

        item = BundleItem.objects.create(
            bundle=bundle,
            product=product,
            quantity=data.quantity,
            position=data.position,
        )
        return 201, item

    @http_put("/{bundle_id}/items/{item_id}", response={200: BundleItemSchema})
    @handle_exceptions
    @log_api_call()
    def update_bundle_item(
        self, request, bundle_id: UUID, item_id: UUID, data: BundleItemUpdateSchema
    ):
        """Update bundle item."""
        item = get_object_or_404(BundleItem, id=item_id, bundle_id=bundle_id)

        if data.product_id:
            item.product = get_object_or_404(Product, id=data.product_id)

        for field, value in data.dict(
            exclude_unset=True, exclude={"product_id"}
        ).items():
            setattr(item, field, value)

        item.save()
        return 200, item

    @http_delete("/{bundle_id}/items/{item_id}", response={204: None})
    @handle_exceptions
    @log_api_call()
    def delete_bundle_item(self, request, bundle_id: UUID, item_id: UUID):
        """Delete bundle item."""
        item = get_object_or_404(BundleItem, id=item_id, bundle_id=bundle_id)
        item.delete()
        return 204, None
