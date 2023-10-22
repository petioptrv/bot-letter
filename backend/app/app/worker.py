import asyncio
import logging
from typing import Optional

from raven import Client
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.data_providers.articles_fetcher import update_articles_database
from app.core.newsletter_creator import generate_newsletter
from app.crud import crud_user
from app.db.session import SessionLocal

client_sentry = Client(settings.SENTRY_DSN)
logging.basicConfig(level=logging.INFO)


@celery_app.task(acks_late=True)
def update_articles_database_task():
    asyncio.run(update_articles_database())


@celery_app.task(acks_late=True)
def generate_all_newsletters():
    db: Optional[Session] = None
    try:
        db = SessionLocal()
        users = crud_user.user.get_all(db=db)
        for user in users:
            for subscription in user.subscriptions:
                celery_app.send_task(
                    name="app.worker.generate_newsletter_task",
                    args=[subscription.newsletter_description, user.id, user.email],
                )
    finally:
        if db is not None:
            db.close()


@celery_app.task(acks_late=True, max_retries=3, retry_backoff=True)
def generate_newsletter_task(newsletter_description: str, user_id: int, email: str):
    asyncio.run(
        generate_newsletter(
            newsletter_description=newsletter_description, user_id=user_id, email=email
        )
    )


if __name__ == "__main__":
    generate_all_newsletters()
