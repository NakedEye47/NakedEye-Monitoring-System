import httpx
from app.config import settings


async def get_youtube_stats() -> dict:
    if not settings.YOUTUBE_API_KEY or not settings.YOUTUBE_CHANNEL_ID:
        return {"error": "YouTube API key or Channel ID not configured"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:

            # Channel stats
            channel_res = await client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={
                    "part": "snippet,statistics,brandingSettings",
                    "id": settings.YOUTUBE_CHANNEL_ID,
                    "key": settings.YOUTUBE_API_KEY,
                }
            )
            channel_data = channel_res.json()

            if not channel_data.get("items"):
                return {"error": "Channel not found"}

            ch = channel_data["items"][0]
            stats = ch["statistics"]
            snippet = ch["snippet"]

            # Latest videos
            videos_res = await client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "channelId": settings.YOUTUBE_CHANNEL_ID,
                    "maxResults": 5,
                    "order": "date",
                    "type": "video",
                    "key": settings.YOUTUBE_API_KEY,
                }
            )
            videos_data = videos_res.json()
            video_ids = [item["id"]["videoId"] for item in videos_data.get("items", [])]

            # Video stats
            video_stats = []
            if video_ids:
                vstats_res = await client.get(
                    "https://www.googleapis.com/youtube/v3/videos",
                    params={
                        "part": "snippet,statistics",
                        "id": ",".join(video_ids),
                        "key": settings.YOUTUBE_API_KEY,
                    }
                )
                vstats_data = vstats_res.json()
                for v in vstats_data.get("items", []):
                    video_stats.append({
                        "id": v["id"],
                        "title": v["snippet"]["title"],
                        "published_at": v["snippet"]["publishedAt"],
                        "thumbnail": v["snippet"]["thumbnails"].get("medium", {}).get("url", ""),
                        "views": int(v["statistics"].get("viewCount", 0)),
                        "likes": int(v["statistics"].get("likeCount", 0)),
                        "comments": int(v["statistics"].get("commentCount", 0)),
                        "url": f"https://www.youtube.com/watch?v={v['id']}",
                    })

            return {
                "channel_name": snippet.get("title", ""),
                "description": snippet.get("description", "")[:200],
                "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                "subscribers": int(stats.get("subscriberCount", 0)),
                "total_views": int(stats.get("viewCount", 0)),
                "video_count": int(stats.get("videoCount", 0)),
                "channel_url": f"https://www.youtube.com/channel/{settings.YOUTUBE_CHANNEL_ID}",
                "latest_videos": video_stats,
            }

    except Exception as e:
        return {"error": str(e)}
