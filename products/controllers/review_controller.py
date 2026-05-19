import logging
from uuid import UUID

from django.db import transaction
from django.shortcuts import get_object_or_404
from ninja.pagination import paginate
from ninja_extra import api_controller, http_delete, http_get, http_post, http_put
from ninja_extra.permissions import IsAuthenticated

from api.decorators import handle_exceptions, log_api_call
from api.exceptions import APIPermissionError as PermissionDeniedError, BadRequestError
from products.models import Product, ProductReview
from products.schemas import (
    ProductReviewCreateSchema,
    ProductReviewSchema,
    ProductReviewUpdateSchema,
)

logger = logging.getLogger(__name__)


@api_controller("/products/reviews", tags=["Product Reviews"])
class ReviewController:
    permission_classes = [IsAuthenticated]

    @http_get("", response={200: list[ProductReviewSchema]})
    @handle_exceptions
    @log_api_call()
    @paginate
    def list_reviews(self, request):
        """Get paginated list of product reviews."""
        reviews = ProductReview.objects.select_related("product", "user").order_by(
            "-created_at"
        )
        return 200, reviews

    @http_get("/{id}", response={200: ProductReviewSchema})
    @handle_exceptions
    @log_api_call()
    def get_review(self, request, id: UUID):
        """Get product review by ID."""
        review = get_object_or_404(
            ProductReview.objects.select_related("product", "user"),
            id=id,
        )
        return 200, review

    @http_get("/products/{product_id}", response={200: list[ProductReviewSchema]})
    @handle_exceptions
    @log_api_call()
    @paginate
    def get_product_reviews(self, request, product_id: str):
        """Get all reviews for a specific product."""
        reviews = (
            ProductReview.objects.filter(product_id=product_id)
            .select_related("product", "user")
            .order_by("-created_at")
        )
        return 200, reviews

    @http_post("", response={201: ProductReviewSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def create_review(self, request, payload: ProductReviewCreateSchema):
        """Create new product review."""
        # Ensure product exists
        product = get_object_or_404(Product, id=payload.product_id)

        # Check if user has already reviewed this product
        if ProductReview.objects.filter(product=product, user=request.user).exists():
            raise BadRequestError("User has already reviewed this product")

        review = ProductReview.objects.create(
            product=product,
            user=request.user,
            rating=payload.rating,
            title=payload.title,
            comment=payload.comment,
        )
        return 201, review

    @http_put("/{id}", response={200: ProductReviewSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def update_review(self, request, id: str, payload: ProductReviewUpdateSchema):
        """Update product review."""
        review = get_object_or_404(ProductReview, id=id)

        # Ensure user owns the review
        if review.user != request.user:
            raise PermissionDeniedError("Not authorized to update this review")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(review, field, value)
        review.save()

        return 200, review

    @http_delete("/{id}", response={204: None})
    @handle_exceptions
    @log_api_call()
    def delete_review(self, request, id: str):
        """Delete product review."""
        review = get_object_or_404(ProductReview, id=id)

        # Ensure user owns the review or is admin
        if review.user != request.user and not request.user.is_staff:
            raise PermissionDeniedError("Not authorized to delete this review")

        review.delete()
        return 204, None

    @http_put("/{id}/verify", response={200: ProductReviewSchema})
    @handle_exceptions
    @log_api_call()
    def verify_review(self, request, id: str):
        """Verify product review (admin only)."""
        if not request.user.is_staff:
            raise PermissionDeniedError("Only administrators can verify reviews")

        review = get_object_or_404(ProductReview, id=id)
        review.is_verified = True
        review.save()

        return 200, review

    @http_put("/{id}/feature", response={200: ProductReviewSchema})
    @handle_exceptions
    @log_api_call()
    def feature_review(self, request, id: str):
        """Feature/unfeature product review (admin only)."""
        if not request.user.is_staff:
            raise PermissionDeniedError("Only administrators can feature reviews")

        review = get_object_or_404(ProductReview, id=id)
        review.is_featured = not review.is_featured
        review.save()

        return 200, review
