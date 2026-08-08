from fastapi import APIRouter

from app.api.v1.routers import billing, dashboard, favorites, health, me, searches, videos
from app.api.v1.routers.webhooks import clerk as clerk_webhooks
from app.api.v1.routers.webhooks import stripe as stripe_webhooks

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(me.router)
api_router.include_router(searches.router)
api_router.include_router(favorites.router)
api_router.include_router(videos.router)
api_router.include_router(dashboard.router)
api_router.include_router(billing.router)
api_router.include_router(clerk_webhooks.router)
api_router.include_router(stripe_webhooks.router)
