import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

celery_app = Celery("encore")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
celery_app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
celery_app.autodiscover_tasks()

celery_app.conf.task_time_limit = 5400
celery_app.conf.task_soft_time_limit = 5340
celery_app.conf.broker_transport_options = {"visibility_timeout": 5400}

@celery_app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")

import threading
from prometheus_client import start_http_server

def start_metrics_server():
    start_http_server(8001)

threading.Thread(target=start_metrics_server, daemon=True).start()
