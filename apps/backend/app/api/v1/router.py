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
from app.api.v1.csv_tools import router as csv_router
from app.api.v1.dynamic_pricing import router as dynamic_pricing_router
from app.api.v1.scheduled_jobs import router as scheduled_jobs_router
from app.api.v1.admin import router as admin_router
from app.api.v1.listing_health import router as listing_health_router
from app.api.v1.profit import router as profit_router
from app.api.v1.action_queue import router as action_queue_router
from app.api.v1.insights import router as insights_router
from app.api.v1.promote import router as promote_router
from app.api.v1.video_generator import router as video_generator_router
from app.api.v1.bulk_create import router as bulk_create_router
from app.api.v1.usage import router as usage_router
from app.api.v1.contact import router as contact_router

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
api_router.include_router(csv_router)
api_router.include_router(dynamic_pricing_router)
api_router.include_router(scheduled_jobs_router)
api_router.include_router(admin_router)
api_router.include_router(listing_health_router)
api_router.include_router(profit_router)
api_router.include_router(action_queue_router)
api_router.include_router(insights_router)
api_router.include_router(promote_router)
api_router.include_router(video_generator_router)
api_router.include_router(bulk_create_router)
api_router.include_router(usage_router)
api_router.include_router(contact_router)
