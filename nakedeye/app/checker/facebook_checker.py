import httpx
from app.config import settings


async def get_facebook_stats() -> dict:
    if not settings.FACEBOOK_ACCESS_TOKEN or not settings.FACEBOOK_PAGE_ID:
        return {"error": "Facebook Access Token or Page ID not configured"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:

            # Page info + followers
            page_res = await client.get(
                f"https://graph.facebook.com/v19.0/{settings.FACEBOOK_PAGE_ID}",
                params={
                    "fields": "name,fan_count,followers_count,picture,about,link",
                    "access_token": settings.FACEBOOK_ACCESS_TOKEN,
                }
            )
            page_data = page_res.json()

            if "error" in page_data:
                return {"error": page_data["error"].get("message", "Facebook API error")}

            # Recent posts
            posts_res = await client.get(
                f"https://graph.facebook.com/v19.0/{settings.FACEBOOK_PAGE_ID}/posts",
                params={
                    "fields": "message,created_time,full_picture,permalink_url,likes.summary(true),comments.summary(true),shares",
                    "limit": 5,
                    "access_token": settings.FACEBOOK_ACCESS_TOKEN,
                }
            )
            posts_data = posts_res.json()

            recent_posts = []
            for post in posts_data.get("data", []):
                recent_posts.append({
                    "message": (post.get("message") or "")[:120],
                    "created_time": post.get("created_time", ""),
                    "picture": post.get("full_picture", ""),
                    "url": post.get("permalink_url", ""),
                    "likes": post.get("likes", {}).get("summary", {}).get("total_count", 0),
                    "comments": post.get("comments", {}).get("summary", {}).get("total_count", 0),
                    "shares": post.get("shares", {}).get("count", 0),
                })

            return {
                "page_name": page_data.get("name", ""),
                "about": page_data.get("about", ""),
                "followers": page_data.get("followers_count", 0),
                "fans": page_data.get("fan_count", 0),
                "picture": page_data.get("picture", {}).get("data", {}).get("url", ""),
                "page_url": page_data.get("link", f"https://www.facebook.com/{settings.FACEBOOK_PAGE_ID}"),
                "recent_posts": recent_posts,
            }

    except Exception as e:
        return {"error": str(e)}
