import hashlib

from django.conf import settings

from pocket.helpers import save_to_redis
from redis_helper import get_from_redis


def save_confirmation_transaction_code(transaction_uuid, code):
    key = f'confirm-transaction:{transaction_uuid}:{settings.SECRET_KEY}'
    key_hash = hashlib.md5(key.encode('utf-8')).hexdigest()
    save_to_redis(key_hash, code, time=settings.VALIDATION_CODE_LIFETIME)


def get_confirmation_transaction_code(transaction_uuid):
    key = f'confirm-transaction:{transaction_uuid}:{settings.SECRET_KEY}'
    key_hash = hashlib.md5(key.encode('utf-8')).hexdigest()
    value = get_from_redis(key_hash)
    return value.decode('utf-8') if value is not None else None
