from celery import shared_task
from backend.services.store_market_ids import store_market_ids
from backend.services.covert_odds_data import convert_odds_format
from backend.services.scaper_service import get_odds, get_tree_record
from backend.services.store_treedata_service import save_tree_data
from backend.services.redis_service import redis_service
from django.core.exceptions import ObjectDoesNotExist
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
        
        # Convert odds to target format with sport_id and event_id
        converted_odds = convert_odds_format(raw_odds, sport_id=sport_id, event_id=event_id)
        
        if not converted_odds:
            print(f"[WARNING] No odds converted for sport_id: {sport_id}, event_id: {event_id}")
            return
        
        # Store converted odds in Redis as JSON
        key = f"odds:{sport_id}:{event_id}"
        
        # Store the single event object (since convert_odds_format now returns a single object)
        redis_service.set_data(key, converted_odds, expire=30)
        
        print(f"[SUCCESS] Converted and stored odds for sport_id: {sport_id}, event_id: {event_id} in Redis: {key}")
        
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


@shared_task
def save_market_ids_task(event_id: str, sport_id: int, password: str):
    """
    Celery task: fetch odds for a given event and store market ids.
    """
    try:
        event = Event.objects.get(event_id=event_id, sport__event_type_id=sport_id)
    except ObjectDoesNotExist:
        print(f"⚠️ Event not found: event_id={event_id}, sport_id={sport_id}")
        return

    try:
        print(f"🚀 Fetching odds for event {event_id}, sport {sport_id}")
        
        # Fetch odds data
        odds_data = get_odds(sport_id, event_id, password)
        

        if not odds_data:
            print(f"⚠️ No odds data returned for event {event_id}")
            return
            
        print(f"✅ Got odds data for event {event_id}, processing market IDs...")
        
        # Store market IDs
        store_market_ids(event, odds_data)
        
        print(f"✅ Completed processing for event '{event.event_name}' ({event.event_id})")
        
    except Exception as e:
        print(f"⚠️ Error in save_market_ids_task for {event_id}: {e}")
        import traceback
        print(f"⚠️ Full error trace:\n{traceback.format_exc()}")


@shared_task
def save_market_ids_for_all_events(password: str):
    events = Event.objects.all()
    for event in events:
        save_market_ids_task.delay(event.event_id, event.sport.event_type_id, password) 