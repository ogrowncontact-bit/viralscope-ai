from fastapi import APIRouter

from app.api.v1.routers import dashboard, favorites, health, me, searches
from app.api.v1.routers.webhooks import clerk as clerk_webhooks

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(me.router)
api_router.include_router(searches.router)
api_router.include_router(favorites.router)
api_router.include_router(dashboard.router)
api_router.include_router(clerk_webhooks.router)
