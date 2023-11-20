import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, crud
from app.api import deps
from app.core.celery_app import celery_app
from app.core.config import settings

router = APIRouter()


@router.get("/can-create", response_model=bool)
def can_create(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> bool:
    """
    Check if the current user can create a subscription.
    """
    return len(current_user.subscriptions) < settings.MAX_SUBSCRIPTIONS


@router.post("/create", response_model=schemas.SubscriptionInDB)
async def create_subscription(
    subscription_in: schemas.SubscriptionCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Create a new subscription.
    """
    if len(current_user.subscriptions) >= settings.MAX_SUBSCRIPTIONS:
        raise HTTPException(
            status_code=400, detail="Maximum number of subscriptions reached."
        )
    if (  # the check cannot be part of the pydantic model because it causes circular import issues with `settings`
        len(subscription_in.newsletter_description)
        > settings.MAX_NEWSLETTER_DESCRIPTION_LENGTH
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Description must be  at most {settings.MAX_NEWSLETTER_DESCRIPTION_LENGTH} characters.",
        )
    if (  # the check cannot be part of the pydantic model because it causes circular import issues with `settings`
        len(subscription_in.newsletter_description)
        < settings.MIN_NEWSLETTER_DESCRIPTION_LENGTH
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Description must be at least {settings.MIN_NEWSLETTER_DESCRIPTION_LENGTH} characters.",
        )
    if (
        crud.subscription.get_by_owner_and_description(
            db=db,
            owner_id=current_user.id,
            newsletter_description=subscription_in.newsletter_description,
        )
        is not None
    ):
        raise HTTPException(
            status_code=409,
            detail="You already have a subscription for this newsletter description.",
        )
    subscription = crud.subscription.create_with_owner(
        db=db, obj_in=subscription_in, owner_id=current_user.id
    )
    return subscription


@router.delete("/delete", response_model=schemas.SubscriptionInDB)
async def delete_subscription(
    subscription_out: schemas.SubscriptionDelete,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Delete a subscription.
    """
    subscription = crud.subscription.delete_by_owner(
        db=db, obj_out=subscription_out, owner_id=current_user.id
    )
    return subscription


@router.get("/can-issue-sample", response_model=bool)
def can_issue_sample(
    subscription: schemas.SubscriptionIssue,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> bool:
    """
    Check if the current user can issue a one-time sample for given subscription.
    """
    db_subscription = crud.subscription.get_by_owner_and_description(
        db=db,
        owner_id=current_user.id,
        newsletter_description=subscription.newsletter_description,
    )
    can_issue = current_user.is_superuser or (db_subscription is not None and db_subscription.sample_available)
    logging.getLogger(__name__).debug(f"can_issue_sample: {can_issue}")
    return can_issue


@router.post("/issue-sample", response_model=schemas.SubscriptionInDB)
async def issue_newsletter_sample(
    subscription: schemas.SubscriptionIssue,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Start a celery task to issue a sample newsletter for a given subscription.
    """
    db_subscription = crud.subscription.get_by_owner_and_description(
        db=db,
        owner_id=current_user.id,
        newsletter_description=subscription.newsletter_description,
    )
    if db_subscription is None:
        raise HTTPException(
            status_code=404,
            detail="You do not have a subscription for this newsletter description.",
        )
    if not current_user.is_superuser and not db_subscription.sample_available:
        raise HTTPException(
            status_code=400,
            detail="You have already issued a one-time sample for this subscription.",
        )
    celery_app.send_task(
        name="app.worker.generate_newsletter_task",
        args=[subscription.newsletter_description, current_user.id, current_user.email],
    )
    subscription_in = schemas.SubscriptionUpdate(sample_available=False or current_user.is_superuser)
    crud.subscription.update(db=db, db_obj=db_subscription, obj_in=subscription_in)

    return db_subscription
