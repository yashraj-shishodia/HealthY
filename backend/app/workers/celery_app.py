import os
import sys
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "healthy_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Enable eager execution in test environment or when under pytest
is_testing = settings.ENVIRONMENT == "testing" or "pytest" in os.environ.get("_", "") or (hasattr(sys, "argv") and sys.argv and any("pytest" in arg for arg in sys.argv))

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_always_eager=True,  # Always execute tasks synchronously in testing/dev to avoid Redis blocking
    task_eager_propagates=True,
)

# Scheduled Periodic Tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    "cleanup-expired-holds-every-minute": {
        "task": "app.workers.tasks.cleanup_expired_holds_task",
        "schedule": 60.0,
    },
    "process-medication-reminders-every-5-minutes": {
        "task": "app.workers.tasks.process_medication_reminders_task",
        "schedule": 300.0,
    },
    "retry-failed-notifications-every-15-minutes": {
        "task": "app.workers.tasks.retry_failed_notifications_task",
        "schedule": 900.0,
    },
}
