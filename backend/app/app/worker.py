import asyncio

from raven import Client

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.newsletter_creator import generate_newsletter
from app.crud import crud_user
from app.db.session import SessionLocal

client_sentry = Client(settings.SENTRY_DSN)


@celery_app.task(acks_late=True)
def generate_all_newsletters():
    try:
        db = SessionLocal()
        users = crud_user.user.get_all(db=db)
        for user in users:
            for subscription in user.subscriptions:
                celery_app.send_task(
                    name="app.worker.generate_newsletter_task",
                    args=[subscription.search_term, user.id],
                )
    finally:
        db.close()


@celery_app.task(acks_late=True)  # todo: test how many times it retries — may rack up OpenAI API costs
def generate_newsletter_task(search_term: str, user_id: int):
    asyncio.run(generate_newsletter(search_term=search_term, user_id=user_id))


if __name__ == "__main__":
    generate_all_newsletters()
