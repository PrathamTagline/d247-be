import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")

# 🔑 This ensures Celery auto-discovers tasks.py inside installed apps
app.autodiscover_tasks([
    "backend.services",
])

@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    from backend.services.tasks import save_tree_data_task
    from backend.services.tasks import save_market_ids_for_all_events
    password = os.getenv("DECRYPTION_KEY")
    # Run immediately once at startup
    sender.send_task("backend.services.tasks.save_tree_data_task")
    sender.send_task("backend.services.tasks.save_market_ids_for_all_events", args=[password])
    # Then run every 10 minutes
    sender.add_periodic_task(
        60.0 * 45,  # seconds
        save_tree_data_task.s(),
        name="Save tree data every 10 min",
    )
    sender.add_periodic_task(
        60.0 * 45,  # seconds
        save_market_ids_for_all_events.s(password=password),
        name="Save market IDs for all events every 2 min",
    )