import logging
from uuid import UUID

from django.db import transaction
from django.shortcuts import get_object_or_404
from ninja.pagination import paginate
from ninja_extra import api_controller, http_get, http_post
from ninja_extra.permissions import IsAuthenticated

from api.decorators import handle_exceptions, log_api_call

from ..models import PriceAction, Product, ProductPriceHistory, ProductVariant
from ..schemas.price_schema import (
    PriceAdjustmentResponseSchema,
    PriceAdjustmentSchema,
    PriceHistorySchema,
)

logger = logging.getLogger(__name__)


@api_controller("/prices", tags=["Prices"], permissions=[IsAuthenticated])
class PriceController:
    @http_get("/{product_id}/history", response={200: list[PriceHistorySchema]})
    @handle_exceptions
    @log_api_call()
    @paginate
    def get_price_history(self, request, product_id: UUID):
        """Get price history for a product."""
        history = ProductPriceHistory.objects.filter(product_id=product_id).order_by(
            "-created_at"
        )
        return 200, history

    @http_get(
        "/{product_id}/variant/{variant_id}/history",
        response={200: list[PriceHistorySchema]},
    )
    @handle_exceptions
    @log_api_call()
    @paginate
    def get_variant_price_history(self, request, product_id: UUID, variant_id: UUID):
        """Get price history for a product variant."""
        history = ProductPriceHistory.objects.filter(
            product_id=product_id, variant_id=variant_id
        ).order_by("-created_at")
        return 200, history

    @http_post("/{product_id}/adjust", response={200: PriceAdjustmentResponseSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def adjust_price(
        self, request, product_id: UUID, adjustment: PriceAdjustmentSchema
    ):
        """Adjust price for a product or variant."""
        product = get_object_or_404(Product, id=product_id)

        if adjustment.variant_id:
            variant = get_object_or_404(ProductVariant, id=adjustment.variant_id)
            previous_price = variant.price
            variant.price = adjustment.new_price

            if adjustment.action == PriceAction.SALE_PRICE:
                variant.compare_at_price = previous_price
            elif adjustment.action == PriceAction.COST_PRICE:
                variant.cost_price = adjustment.new_price

            variant.save()

            history = ProductPriceHistory.objects.create(
                product=product,
                variant=variant,
                action=adjustment.action,
                previous_price=previous_price,
                new_price=adjustment.new_price,
                reason=adjustment.reason,
                notes=adjustment.notes,
            )
        else:
            previous_price = product.price
            product.price = adjustment.new_price

            if adjustment.action == PriceAction.SALE_PRICE:
                product.compare_at_price = previous_price
            elif adjustment.action == PriceAction.COST_PRICE:
                product.cost_price = adjustment.new_price

            product.save()

            history = ProductPriceHistory.objects.create(
                product=product,
                action=adjustment.action,
                previous_price=previous_price,
                new_price=adjustment.new_price,
                reason=adjustment.reason,
                notes=adjustment.notes,
            )

        return 200, {
            "success": True,
            "message": "Price adjusted successfully",
            "history": history,
        }

    @http_post(
        "/{product_id}/bulk-adjust", response={200: list[PriceAdjustmentResponseSchema]}
    )
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def bulk_adjust_prices(
        self, request, product_id: UUID, adjustments: list[PriceAdjustmentSchema]
    ):
        """Bulk adjust prices for product variants."""
        product = get_object_or_404(Product, id=product_id)
        results = []

        for adjustment in adjustments:
            if adjustment.variant_id:
                variant = get_object_or_404(ProductVariant, id=adjustment.variant_id)
                previous_price = variant.price
                variant.price = adjustment.new_price

                if adjustment.action == PriceAction.SALE_PRICE:
                    variant.compare_at_price = previous_price
                elif adjustment.action == PriceAction.COST_PRICE:
                    variant.cost_price = adjustment.new_price

                variant.save()

                history = ProductPriceHistory.objects.create(
                    product=product,
                    variant=variant,
                    action=adjustment.action,
                    previous_price=previous_price,
                    new_price=adjustment.new_price,
                    reason=adjustment.reason,
                    notes=adjustment.notes,
                )

                results.append(
                    {
                        "success": True,
                        "message": f"Price adjusted successfully for variant {variant.id}",
                        "history": history,
                    }
                )

        return 200, results
