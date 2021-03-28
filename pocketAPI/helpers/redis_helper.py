import redis
from django.conf import settings


def save_to_redis(key, value, time=60):
    key = f'{settings.REDIS_PREFIX}-{key}'
    redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                       port=settings.REDIS_PORT)
    redis_instance.set(key, value, time)


def get_from_redis(key):
    key = f'{settings.REDIS_PREFIX}-{key}'
    redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                       port=settings.REDIS_PORT)
    return redis_instance.get(key)
