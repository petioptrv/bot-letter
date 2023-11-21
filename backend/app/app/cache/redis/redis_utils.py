from app.base_types import Config


class RedisConfig(Config):
    redis_host: str
    redis_port: int
    redis_password: str
    cache_ttl_days: int
    cache_items_per_user: int


redis_config = RedisConfig()
