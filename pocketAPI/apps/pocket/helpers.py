import hashlib
import random

from django.contrib.auth import get_user_model
from django.conf import settings

from redis_helper import save_to_redis, get_from_redis

UserModel = get_user_model()


def generate_code(length):
    code = ''
    for _ in range(length):
        code += str(random.randint(0, 9))
    return code


def save_deletion_pocket_code(pocket_uuid, code):
    key = f'deletion-pocket:{pocket_uuid}:{settings.SECRET_KEY}'
    key_hash = hashlib.md5(key.encode('utf-8')).hexdigest()
    print(settings.VALIDATION_CODE_LIFETIME)
    save_to_redis(key_hash, code, time=settings.VALIDATION_CODE_LIFETIME)


def get_deletion_pocket_code(pocket_uuid):
    key = f'deletion-pocket:{pocket_uuid}:{settings.SECRET_KEY}'
    key_hash = hashlib.md5(key.encode('utf-8')).hexdigest()
    value = get_from_redis(key_hash)
    return value.decode('utf-8') if value is not None else None

