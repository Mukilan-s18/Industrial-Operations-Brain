import os
from celery import Celery

REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

# Initialize Celery app
celery_app = Celery(
    "industrial_copilot",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["ingestion.utils.task_manager"],
)

# Optional configuration, e.g. strict typing or result backend settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
