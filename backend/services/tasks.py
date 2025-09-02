from celery import shared_task
from backend.services.covert_odds_data import convert_odds_format
from backend.services.scaper_service import get_odds, get_tree_record
from backend.services.store_treedata_service import save_tree_data
from backend.services.redis_service import redis_service
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
    Task to fetch odds, convert format, and store in Redis
    """
    try:
        # Fetch raw odds data
        raw_odds = get_odds(sport_id, event_id, os.getenv("DECRYPTION_KEY"))
        
        if not raw_odds:
            print(f"[WARNING] No odds data received for sport_id: {sport_id}, event_id: {event_id}")
            return
        
        # Convert odds to target format
        converted_odds = convert_odds_format(raw_odds)
        
        if not converted_odds:
            print(f"[WARNING] No odds converted for sport_id: {sport_id}, event_id: {event_id}")
            return
        
        # Store converted odds in Redis as JSON
        key = f"odds:{sport_id}:{event_id}"
        
        # If you want to store as a single object instead of array, use the first item
        if len(converted_odds) == 1:
            # Store single event object
            redis_service.set_data(key, converted_odds[0], expire=300000)
        else:
            # Store as array if multiple events
            redis_service.set_data(key, converted_odds, expire=300000)
        
        print(f"[SUCCESS] Converted and stored {len(converted_odds)} odds events in Redis: {key}")
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch/convert/store odds for sport_id: {sport_id}, event_id: {event_id} - {e}")


@shared_task
def fetch_odds_for_all_events():
    """
    Fetch odds for all events dynamically from the database.
    """
    try:
        events = Event.objects.select_related("sport").all()
        
        total_events = events.count()
        print(f"[INFO] Starting odds fetch for {total_events} events")
        
        for event in events:
            sport_id = event.sport.event_type_id  # your mapping
            event_id = event.event_id
            
            # Queue the individual fetch task
            fetch_and_store_odds.delay(sport_id, event_id)
        
        print(f"[SUCCESS] Queued odds fetch tasks for {total_events} events")
        
    except Exception as e:
        print(f"[ERROR] Failed to queue odds fetch tasks: {e}")