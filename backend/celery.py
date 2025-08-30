import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(["backend.services"])

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from backend.services.tasks import refresh_g_token
    sender.add_periodic_task(600.0, refresh_g_token.s(), name="refresh g_token every 10 min")
