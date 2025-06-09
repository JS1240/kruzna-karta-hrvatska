import redis

from .config import settings

redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)


def get_cache():
    return redis_client
