from celery import shared_task
from django.core.cache import cache
from backend.services.gtoken_get_service import get_cookie_token


@shared_task(name="backend.services.tasks.refresh_g_token")
def refresh_g_token():
    token = get_cookie_token()
    if token:
        cache.set("g_token", token, timeout=600)  # overwrite in Redis
        return f"✅ g_token refreshed: {token[:20]}..."
    return "❌ Failed to fetch g_token"


def get_latest_g_token():
    """Fetch latest g_token from Redis. If missing, auto-refresh it."""
    token = cache.get("g_token")
    if not token:
        token = get_cookie_token()
        if token:
            cache.set("g_token", token, timeout=600)
    return token
