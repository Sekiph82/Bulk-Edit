from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.billing import router as billing_router
from app.api.v1.etsy import router as etsy_router
from app.api.v1.shops import router as shops_router
from app.api.v1.listings import router as listings_router
from app.api.v1.bulk_edit import router as bulk_edit_router
from app.api.v1.bulk_edit_media import router as bulk_edit_media_router
from app.api.v1.bulk_edit_variations import router as bulk_edit_variations_router
from app.api.v1.ai import router as ai_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(billing_router)
api_router.include_router(etsy_router)
api_router.include_router(shops_router)
api_router.include_router(listings_router)
api_router.include_router(bulk_edit_router)
api_router.include_router(bulk_edit_media_router)
api_router.include_router(bulk_edit_variations_router)
api_router.include_router(ai_router)
