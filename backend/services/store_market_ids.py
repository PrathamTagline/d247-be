# Fixed version of your store_market_ids function in backend/services/__init__.py

from django.db import transaction
from sports.models import Event, Competition

def store_market_ids(event: Event, data: dict) -> None:
    """
    Extract all `mid` values from the given odds payload and
    store them in the Event model (and update competition count if present).
    """
    try:
        if not data or not isinstance(data, dict):
            print(f"⚠️ No valid data received for event {event.event_name} ({event.event_id})")
            return

        mids = []

        # ✅ markets are in top-level odds_data["data"]
        for market in data.get("data") or []:
            mid = market.get("mid")
            if mid:
                mids.append(mid)

        # Deduplicate
        mids = list(set(mids))
        print(mids)

        with transaction.atomic():
            event.market_ids = mids
            event.market_count = len(mids)
            event.save(update_fields=["market_ids", "market_count"])

            # Also update related competition market_count
            if event.competition_id:
                Competition.objects.filter(id=event.competition_id).update(
                    market_count=event.market_count
                )

        print(f"✅ Stored {len(mids)} market IDs for event {event.event_name} ({event.event_id})")

    except Exception as e:
        print(f"⚠️ Error extracting & saving mids for event {event.id}: {e}")
        import traceback
        print(f"⚠️ Full traceback: {traceback.format_exc()}")
