"""Business logic for products."""

import logging

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import QuerySet, Subquery

from api.config.constants import MAX_SEARCH_RESULTS
from products.models import Product

logger = logging.getLogger(__name__)


class ProductService:
    """Business logic for products."""

    @staticmethod
    def search_products(query: str) -> QuerySet:
        """Search active products by weighted full-text relevance.

        Searches across the product name (weight A), description
        (weight B), and tag names (weight C). Results are ranked by
        SearchRank with cover density so exact phrase and near matches
        outrank keyword-only matches, and capped at MAX_SEARCH_RESULTS.

        The cap uses a top-N subquery instead of a slice so callers can
        still reorder the returned queryset (the search_and_filter
        decorator applies an explicit ``ordering`` param on top of it;
        Django forbids order_by() after a slice).
        """
        vector = (
            SearchVector("name", weight="A")
            + SearchVector("description", weight="B")
            + SearchVector("tags__name", weight="C")
        )
        search_query = SearchQuery(query)
        base = Product.objects.annotate(
            rank=SearchRank(vector, search_query, cover_density=True)
        ).filter(is_active=True, rank__gt=0)
        top_ids = base.order_by("-rank").values("pk")[:MAX_SEARCH_RESULTS]
        return base.filter(pk__in=Subquery(top_ids)).order_by("-rank").distinct()
