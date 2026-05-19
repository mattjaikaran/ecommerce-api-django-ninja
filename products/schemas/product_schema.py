from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ninja import Schema
from pydantic import Field, validator

from .collection_schema import CollectionSchema
from .product_option_schema import ProductImageSchema, ProductVariantSchema
from .review_schema import ReviewSchema
from .tag_schema import TagSchema


class ProductSchema(Schema):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    category_id: UUID
    type: str = "physical"
    tax_class: str = "standard"
    shipping_class: str = "standard"
    price: Decimal = Field(ge=0)
    compare_at_price: Decimal | None = None
    cost_price: Decimal | None = None
    quantity: int = 0
    low_stock_threshold: int = 10
    weight: Decimal | None = None
    length: Decimal | None = None
    width: Decimal | None = None
    height: Decimal | None = None
    digital_file: str | None = None
    download_limit: int | None = None
    is_active: bool = True
    status: str = "draft"
    featured: bool = False
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None
    meta_data: dict = {}
    variants: list[ProductVariantSchema]
    images: list[ProductImageSchema]
    reviews: list[ReviewSchema]
    tags: list[TagSchema]
    collections: list[CollectionSchema]
    created_at: datetime
    updated_at: datetime

    @validator("compare_at_price")
    def compare_at_price_must_be_greater_than_price(cls, v, values):
        if v is not None and "price" in values and v <= values["price"]:
            raise ValueError("compare_at_price must be greater than price")
        return v


class ProductCreateSchema(Schema):
    name: str
    slug: str
    description: str | None = None
    category_id: UUID
    type: str = "physical"
    tax_class: str = "standard"
    shipping_class: str = "standard"
    price: Decimal = Field(ge=0)
    compare_at_price: Decimal | None = None
    cost_price: Decimal | None = None
    quantity: int = 0
    low_stock_threshold: int = 10
    weight: Decimal | None = None
    length: Decimal | None = None
    width: Decimal | None = None
    height: Decimal | None = None
    digital_file: str | None = None
    download_limit: int | None = None
    is_active: bool = True
    status: str = "draft"
    featured: bool = False
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None
    meta_data: dict = {}


class ProductListSchema(Schema):
    id: UUID
    name: str
    slug: str
    price: Decimal = Field(ge=0)
    compare_at_price: Decimal | None = None
    status: str = "draft"
    featured: bool = False
    is_active: bool = True
    category_id: UUID
    thumbnail: str | None = None
    created_at: datetime
    updated_at: datetime

    @validator("thumbnail", pre=True)
    def get_thumbnail(cls, v, values):
        """Get the first image URL as thumbnail."""
        if hasattr(values.get("source"), "images"):
            images = values.get("source").images.all()
            if images:
                return images[0].image
        return None

    @validator("compare_at_price")
    def compare_at_price_must_be_greater_than_price(cls, v, values):
        if v is not None and "price" in values and v <= values["price"]:
            raise ValueError("compare_at_price must be greater than price")
        return v


class ProductUpdateSchema(Schema):
    name: str
    slug: str
    description: str | None = None
    category_id: UUID
    type: str = "physical"
    tax_class: str = "standard"
    shipping_class: str = "standard"
    price: Decimal = Field(ge=0)
    compare_at_price: Decimal | None = None
    cost_price: Decimal | None = None
    quantity: int = 0
    low_stock_threshold: int = 10
    weight: Decimal | None = None
    length: Decimal | None = None
    width: Decimal | None = None
    height: Decimal | None = None
    digital_file: str | None = None
    download_limit: int | None = None
