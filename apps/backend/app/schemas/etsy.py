from pydantic import BaseModel
from datetime import datetime


class EtsyAuthorizeResponse(BaseModel):
    authorization_url: str


class EtsyShopResponse(BaseModel):
    id: str
    organization_id: str
    etsy_shop_id: str
    shop_name: str | None
    is_connected: bool
    last_synced_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EtsyShopsResponse(BaseModel):
    shops: list[EtsyShopResponse]
    total: int


class EtsyDisconnectResponse(BaseModel):
    message: str
