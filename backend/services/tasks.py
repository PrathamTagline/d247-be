from celery import shared_task
from backend.services.redis_service import set_data
from backend.services.scaper_service import get_odds, get_tree_record
from backend.services.store_treedata_service import save_tree_data

import os

from sports.models import Event

@shared_task
def save_tree_data_task():
    """Periodic task to fetch and save tree data"""
    from django.conf import settings
    data = get_tree_record(os.getenv("DECRYPTION_KEY"))
    if "error" not in data:
        save_tree_data(data)
    return "Tree data saved successfully"

@shared_task
def fetch_and_store_odds(sport_id: int, event_id: int):
    """
    Task to fetch odds and store in Redis
    """
    try:
        odds = get_odds(sport_id, event_id, os.getenv("DECRYPTION_KEY"))
        key = f"odds:{sport_id}:{event_id}"
        set_data(key, odds, expire=300000)  # expire in 3 sec
        print(f"[SUCCESS] Stored odds in Redis: {key}")
    except Exception as e:
        print(f"[ERROR] Failed to fetch/store odds: {e}")


@shared_task
def fetch_odds_for_all_events():
    """
    Fetch odds for all events dynamically from the database.
    """
    events = Event.objects.select_related("sport").all()
    
    for event in events:
        sport_id = event.sport.event_type_id  # your mapping
        event_id = event.event_id
        fetch_and_store_odds.delay(sport_id, event_id)