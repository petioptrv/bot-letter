from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, crud
from app.api import deps
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
        len(subscription_in.newsletter_description) > settings.MAX_NEWSLETTER_DESCRIPTION_LENGTH
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Description must be  at most {settings.MAX_NEWSLETTER_DESCRIPTION_LENGTH} characters."
        )
    if (  # the check cannot be part of the pydantic model because it causes circular import issues with `settings`
        len(subscription_in.newsletter_description) < settings.MIN_NEWSLETTER_DESCRIPTION_LENGTH
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Description must be at least {settings.MIN_NEWSLETTER_DESCRIPTION_LENGTH} characters."
        )
    if crud.subscription.get_by_owner_and_description(
        db=db,
        owner_id=current_user.id,
        newsletter_description=subscription_in.newsletter_description,
    ) is not None:
        raise HTTPException(
            status_code=409, detail="You already have a subscription for this newsletter description."
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
