from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.cache.redis.redis_utils import redis_config


def get_user(request: Request) -> str:
    return get_remote_address(request=request)


per_user_limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"redis://{redis_config.redis_host}:{redis_config.redis_port}",
    storage_options={"password": redis_config.redis_password},
)
