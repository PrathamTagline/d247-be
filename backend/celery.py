import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")

# 🔑 This ensures Celery auto-discovers tasks.py inside installed apps
app.autodiscover_tasks([
    "backend.services",
])
