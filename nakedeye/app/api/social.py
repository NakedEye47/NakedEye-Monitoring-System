from fastapi import APIRouter
from app.checker.youtube_checker import get_youtube_stats
from app.checker.facebook_checker import get_facebook_stats
from app.config import settings

router = APIRouter(prefix="/social", tags=["social"])


@router.get("/youtube")
async def youtube_stats():
    return await get_youtube_stats()


@router.get("/facebook")
async def facebook_stats():
    return await get_facebook_stats()


@router.get("/config")
async def social_config():
    """Return masked config status — never expose actual keys."""
    return {
        "youtube_configured": bool(settings.YOUTUBE_API_KEY and settings.YOUTUBE_CHANNEL_ID),
        "facebook_configured": bool(settings.FACEBOOK_ACCESS_TOKEN and settings.FACEBOOK_PAGE_ID),
        "youtube_channel_id": settings.YOUTUBE_CHANNEL_ID,
        "facebook_page_id": settings.FACEBOOK_PAGE_ID,
    }
