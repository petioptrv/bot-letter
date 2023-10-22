from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery("worker", broker=f"amqp://guest@{settings.QUEUE_URL}//")
celery_app.conf.timezone = settings.TIMEZONE

celery_app.conf.task_routes = {
    "app.worker.update_articles_database_task": "main-queue",
    "app.worker.generate_newsletter_task": "main-queue",
    "app.worker.generate_all_newsletters": "main-queue",
}
hour, minute = settings.NEWSLETTER_TIME.split(":")
celery_app.conf.beat_schedule = {
    "update-articles-database": {
        "task": "app.worker.update_articles_database_task",
        "schedule": crontab(minute="*/15"),
        "args": (),
    },
    "generate-all-newsletters": {
        "task": "app.worker.generate_all_newsletters",
        "schedule": crontab(hour=hour, minute=minute),
        "args": (),
    },
}
