from sports.models import Sport, Competition, Event
from django.db import transaction
from datetime import datetime


def save_tree_data(tree_data: dict):
    """
    Save tree data into Sport, Competition, and Event models.
    Handles both t1 (Sport → Competition → Event) and t2 (Sport → Event).
    Insert-only: if already exists, skip (no updates).
    """

    with transaction.atomic():
        sports_data = tree_data.get("data") or {}

        # --- Handle T1 ---
        for sport_item in sports_data.get("t1") or []:
            print("Processing sport (T1):", sport_item.get("name"))

            # Check Sport by event_type_id + tree
            sport = Sport.objects.filter(
                event_type_id=sport_item.get("etid"),
                tree="t1"
            ).first()

            if not sport:
                sport = Sport.objects.create(
                    event_type_id=sport_item.get("etid"),
                    oid=sport_item.get("oid"),
                    tree="t1",
                    name=sport_item.get("name") or "",
                )

            # Competitions
            for comp_item in sport_item.get("children") or []:
                competition = Competition.objects.filter(
                    competition_id=comp_item.get("cid"),
                    sport=sport
                ).first()

                if not competition:
                    competition = Competition.objects.create(
                        competition_id=comp_item.get("cid"),
                        competition_name=comp_item.get("name") or "",
                        competition_region=comp_item.get("region") or "",
                        sport=sport,
                    )

                # Events inside Competition
                for event_item in comp_item.get("children") or []:
                    event_exists = Event.objects.filter(
                        event_id=event_item.get("gmid")
                    ).exists()

                    if not event_exists:
                        Event.objects.create(
                            event_id=event_item.get("gmid"),
                            event_name=event_item.get("name") or "",
                            sport=sport,
                            competition=competition,
                        )

        # --- Handle T2 ---
        for sport_item in sports_data.get("t2") or []:
            print("Processing sport (T2):", sport_item.get("name"))

            # Check Sport by event_type_id + tree
            sport = Sport.objects.filter(
                event_type_id=sport_item.get("etid"),
                tree="t2"
            ).first()

            if not sport:
                sport = Sport.objects.create(
                    event_type_id=sport_item.get("etid"),
                    oid=sport_item.get("oid"),
                    tree="t2",
                    name=sport_item.get("name") or "",
                )

            # Events directly under Sport
            for event_item in sport_item.get("children") or []:
                event_exists = Event.objects.filter(
                    event_id=event_item.get("gmid")
                ).exists()

                if not event_exists:
                    event_date = None
                    sdatetime = event_item.get("sdatetime")
                    if sdatetime:
                        try:
                            event_date = datetime.strptime(sdatetime, "%m/%d/%Y %I:%M:%S %p")
                        except Exception:
                            print(f"⚠️ Failed to parse date: {sdatetime}")

                    Event.objects.create(
                        event_id=event_item.get("gmid"),
                        event_name=event_item.get("name") or "",
                        sport=sport,
                        event_open_date=event_date,
                    )
