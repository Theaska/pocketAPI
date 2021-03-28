import hashlib
from enum import IntEnum

from django.conf import settings
from django.db import transaction, models
from django.utils.translation import ugettext_lazy as _

from pocket.helpers import save_to_redis
from redis_helper import get_from_redis
from transactions.exceptions import TransactionError


def save_confirmation_transaction_code(transaction_uuid, code):
    key = f'confirm-transaction:{transaction_uuid}:{settings.SECRET_KEY}'
    key_hash = hashlib.md5(key.encode('utf-8')).hexdigest()
    save_to_redis(key_hash, code, time=settings.VALIDATION_CODE_LIFETIME)


def get_confirmation_transaction_code(transaction_uuid):
    key = f'confirm-transaction:{transaction_uuid}:{settings.SECRET_KEY}'
    key_hash = hashlib.md5(key.encode('utf-8')).hexdigest()
    value = get_from_redis(key_hash)
    return value.decode('utf-8') if value is not None else None


class ActionTransactions(IntEnum):
    REFILL = 1  # пополнение
    DEBIT = 2  # списание

    @classmethod
    def choices(cls):
        return tuple((obj.value, obj.name) for obj in cls)

    @classmethod
    def dict(cls):
        return dict(cls.choices())


class TransactionStatus(IntEnum):
    CREATED = 1
    IN_PROCESS = 2
    CONFIRMED = 3
    FINISHED = 4
    CANCELLED = 5

    @classmethod
    def choices(cls):
        return ((obj.value, obj.name) for obj in cls)

    @classmethod
    def dict(cls):
        return dict(cls.choices())


class StatusMixin(models.Model):
    status = models.PositiveIntegerField(
        _('status'),
        choices=TransactionStatus.choices(),
        default=TransactionStatus.CREATED
    )

    class Meta:
        abstract = True

    @property
    def status_name(self):
        return TransactionStatus.dict()[self.status]

    def change_status(self, new_status: TransactionStatus):
        if self.status == new_status:
            return
        change_status_method = getattr(self, 'set_{}'.format(new_status.name.lower()))
        change_status_method()
        self.save()

    def set_created(self):
        raise TransactionError('Created status is set automatically')

    def set_in_process(self):
        if self.status == TransactionStatus.CREATED:
            self.status = TransactionStatus.IN_PROCESS
        else:
            error_msg = 'Can change status as in progress only with status {}'.format(TransactionStatus.CREATED.name)
            raise TransactionError(error_msg)

    def set_confirmed(self):
        if self.status == TransactionStatus.IN_PROCESS:
            self.status = TransactionStatus.CONFIRMED
        else:
            error_msg = 'Can confirm transaction only with status {}'.format(TransactionStatus.IN_PROCESS.name)
            raise TransactionError(error_msg)

    def set_finished(self):
        if self.status == TransactionStatus.CONFIRMED:
            self.status = TransactionStatus.FINISHED
        else:
            error_msg = 'Can finish transaction only with status {}'.format(TransactionStatus.CONFIRMED.name)
            raise TransactionError(error_msg)

    def set_cancelled(self):
        self.status = TransactionStatus.CANCELLED

