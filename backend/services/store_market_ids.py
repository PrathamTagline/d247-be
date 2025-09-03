from django.db import transaction
from sports.models import Event, Competition

def store_market_ids(event: Event, data: dict) -> None:
    """
    Extract all `mid` values from the given odds payload and
    store them in the Event model (and update competition count if present).
    """
    try:
        mids = []
        odds_root = data.get("odds", {})
        for market in odds_root.get("data", []):
            mid = market.get("mid")
            if mid:
                mids.append(mid)

        # remove duplicates
        mids = list(set(mids))

        with transaction.atomic():
            event.market_ids = mids
            event.market_count = len(mids)
            event.save(update_fields=["market_ids", "market_count"])

            # also update related competition market_count
            if event.competition_id:
                Competition.objects.filter(id=event.competition_id).update(
                    market_count=event.market_count
                )

    except Exception as e:
        print(f"⚠️ Error extracting & saving mids for event {event.id}: {e}")
