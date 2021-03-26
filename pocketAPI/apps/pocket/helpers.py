import random

import redis
from django.contrib.auth import get_user_model

from project import settings
from .conf import VALIDATION_CODE_LIFETIME

UserModel = get_user_model()


def generate_code(length):
    code = ''
    for _ in range(length):
        code += str(random.randint(0, 9))
    return code


def save_deletion_pocket_code(pocket_uuid, code):
    key = f'deletion-pocket:{pocket_uuid}'
    save_to_redis(key, code)


def get_deletion_pocket_code(pocket_uuid):
    key = f'deletion-pocket:{pocket_uuid}'
    value = get_from_redis(key)
    print(value)
    return value.decode('utf-8') if value is not None else None


def save_to_redis(key, value, time=VALIDATION_CODE_LIFETIME):
    key = f'{settings.REDIS_PREFIX}-{key}'
    redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                       port=settings.REDIS_PORT)
    redis_instance.set(key, value, time)


def get_from_redis(key):
    key = f'{settings.REDIS_PREFIX}-{key}'
    redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                       port=settings.REDIS_PORT)
    return redis_instance.get(key)
