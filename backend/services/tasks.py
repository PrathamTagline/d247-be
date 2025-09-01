from celery import shared_task
from backend.services.scaper_service import get_tree_record
from backend.services.store_treedata_service import save_tree_data

import os

@shared_task
def save_tree_data_task():
    """Periodic task to fetch and save tree data"""
    from django.conf import settings
    data = get_tree_record(os.getenv("DECRYPTION_KEY"))
    if "error" not in data:
        save_tree_data(data)
    return "Tree data saved successfully"
