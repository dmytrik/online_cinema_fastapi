from celery import Celery
from celery.schedules import crontab
from core.config import settings
from app.accounts.tasks import check_expired_activation_tokens

app = Celery(
    "core",
    broker=settings.CELERY_BROKER,
    backend=settings.CELERY_BACKEND,
)

app.conf.update(
    timezone=settings.CELERY_TIMEZONE,
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    broker_connection_retry_on_startup=settings.CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP,
)

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "delete_expired_tokens_every_10_minutes": {
        "task": "app.accounts.tasks.check_expired_activation_tokens",
        "schedule": crontab(minute="*/1"),
    }
}
