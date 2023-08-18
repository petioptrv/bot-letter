from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import Response

from app import models, schemas, crud
from app.api import deps
from app.base_types import NewsArticleSearchResults
from app.cache.redis.aio_redis_cache import AioRedisCache
from app.cache.redis.redis_utils import redis_config
from app.core.api_provider import APIProvider
from app.core.config import settings
from app.core.data_providers.news_data_io.news_data_io import NewsDataIO
from app.core.data_providers.news_data_io.news_data_io_utils import (
    news_data_io_config,
)
from app.rate_limiter import per_user_limiter

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


@router.get("/search", response_model=NewsArticleSearchResults)
@per_user_limiter.limit("10/day")
async def search(
    request: Request,
    response: Response,
    search_term: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> NewsArticleSearchResults:
    """
    Get the current user's subscription search.
    """
    if len(search_term) == 0:
        raise HTTPException(status_code=400, detail="Search term cannot be empty.")

    api_provider = APIProvider()
    data_provider = NewsDataIO(api_provider=api_provider, config=news_data_io_config)
    try:
        results = await data_provider.get_last_day_news(
            topic=search_term, max_page_count=settings.MAX_SUBSCRIPTION_SEARCH_RESULTS
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get search results.")
    return results


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
        raise HTTPException(status_code=400, detail="Maximum number of subscriptions reached.")
    subscription = crud.subscription.create_with_owner(db=db, obj_in=subscription_in, owner_id=current_user.id)
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
    cache = AioRedisCache(config=redis_config)
    await cache.initialize()
    await cache.clear_all_items(search_term=subscription_out.search_term)
    return subscription
