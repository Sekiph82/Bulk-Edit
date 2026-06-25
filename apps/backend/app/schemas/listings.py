from pydantic import BaseModel
from datetime import datetime
from typing import Any


class SyncJobResponse(BaseModel):
    sync_job_id: str
    status: str
    processed_items: int
    total_items: int
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ListingImageResponse(BaseModel):
    id: str
    listing_id: str
    etsy_image_id: str | None
    url_fullxfull: str | None
    url_570xN: str | None
    url_170x135: str | None
    alt_text: str | None
    rank: int | None
    width: int | None
    height: int | None

    model_config = {"from_attributes": True}


class ListingVideoResponse(BaseModel):
    id: str
    listing_id: str
    etsy_video_id: str | None
    video_url: str | None
    thumbnail_url: str | None
    rank: int | None

    model_config = {"from_attributes": True}


class ListingVariationResponse(BaseModel):
    id: str
    listing_id: str
    etsy_product_id: str | None
    sku: str | None
    property_name: str | None
    value_name: str | None
    price_amount: int | None
    price_divisor: int | None
    currency_code: str | None
    quantity: int | None
    is_available: bool

    model_config = {"from_attributes": True}


class ListingListItemResponse(BaseModel):
    id: str
    organization_id: str
    etsy_shop_id: str
    etsy_listing_id: str
    title: str | None
    state: str | None
    price_amount: int | None
    price_divisor: int | None
    currency_code: str | None
    quantity: int | None
    has_variations: bool
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ListingDetailResponse(ListingListItemResponse):
    description: str | None
    url: str | None
    sku: str | None
    tags: Any
    materials: Any
    taxonomy_id: str | None
    section_id: str | None
    shipping_profile_id: str | None
    return_policy_id: str | None
    processing_min: int | None
    processing_max: int | None
    who_made: str | None
    when_made: str | None
    is_supply: bool | None
    is_customizable: bool | None
    is_personalizable: bool | None
    personalization_instructions: str | None
    item_weight: Any
    item_weight_unit: str | None
    item_length: Any
    item_width: Any
    item_height: Any
    item_dimensions_unit: str | None
    etsy_updated_at: datetime | None

    model_config = {"from_attributes": True}


class ListingPageResponse(BaseModel):
    items: list[ListingListItemResponse]
    page: int
    per_page: int
    total: int
