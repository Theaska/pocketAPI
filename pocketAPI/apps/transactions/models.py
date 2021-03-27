from enum import IntEnum
import uuid

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from email_helpers import create_email_template
from pocket.models import Pocket
from .exceptions import TransactionError


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
    FINISHED = 3
    CANCELLED = 4

    @classmethod
    def choices(cls):
        return ((obj.value, obj.name) for obj in cls)

    @classmethod
    def dict(cls):
        return dict(cls.choices())


class TransactionQuerySet(models.QuerySet):
    def filter(self, *args, **kwargs):
        return super().filter(pocket__is_archived=False, *args, **kwargs)

    def active(self):
        return self.filter(Q(status=TransactionStatus.CREATED) | Q(status=TransactionStatus.IN_PROCESS))

    def created(self):
        return self.filter(status=TransactionStatus.CREATED)

    def in_progress(self):
        return self.filter(status=TransactionStatus.IN_PROCESS)

    def finished(self):
        return self.filter(status=TransactionStatus.FINISHED)

    def cancelled(self):
        return self.filter(status=TransactionStatus.CANCELLED)


class PocketTransaction(models.Model):
    pocket = models.ForeignKey(Pocket, verbose_name=_('Pocket'), on_delete=models.CASCADE, related_name='transactions')
    uuid = models.UUIDField(_('UUID'), default=uuid.uuid4, unique=True)
    sum = models.FloatField(_('sum'), validators=[MinValueValidator(0), MaxValueValidator(100000)])
    action = models.PositiveIntegerField(
        _('action'),
        choices=ActionTransactions.choices()
    )
    status = models.PositiveIntegerField(
        _('status'),
        choices=TransactionStatus.choices(),
        default=TransactionStatus.CREATED
    )
    date_created = models.DateTimeField(_('date created'), auto_now_add=True)
    date_updated = models.DateTimeField(_('date updated'), auto_now=True)
    comment = models.TextField(_('comment'), blank=True, null=True)

    objects = TransactionQuerySet.as_manager()

    @property
    def status_name(self):
        return TransactionStatus.dict()[self.status]

    @property
    def action_name(self):
        return ActionTransactions.dict()[self.action]

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.pocket.is_archived:
            raise TransactionError('Can not create transaction for archived pocket')
        super().save(force_insert, force_update, using, update_fields)

    @transaction.atomic
    def activate(self):
        if self.status == TransactionStatus.FINISHED or self.status == TransactionStatus.CANCELLED:
            raise TransactionError('Can not activate transaction with status {}'.format(self.status_name))
        elif self.pocket.is_archived:
            raise TransactionError('Can not activate transaction for archived pocket')

        try:
            if self.action == ActionTransactions.DEBIT:
                self.pocket.debit(self.sum)
            else:
                self.pocket.refill(self.sum)
        except Exception as exc:
            raise TransactionError(str(exc))
        else:
            self.action = TransactionStatus.FINISHED
            self.save()

    @transaction.atomic
    def cancel(self):
        if not self.status == TransactionStatus.FINISHED:
            self.status = TransactionStatus.CANCELLED
            self.save()
        else:
            raise TransactionError('Can not cancel finished transaction')

    @transaction.atomic
    def delete(self, using=None, keep_parents=False):
        if self.status == TransactionStatus.CANCELLED or self.status == TransactionStatus.FINISHED:
            super().delete(using, keep_parents)
        else:
            raise TransactionError('Can delete transaction only with status CANCELLED or FINISHED')

    def send_confirmation_code(self, code):
        """
            Send confirmation code for confirm transaction
        """
        current_site = Site.objects.get_current()
        self.pocket.user.email_user(fail_silently=True,
                                    subject=_('Confirm deletion pocket in {domain}'.format(domain=current_site.domain)),
                                    message='email confirmation',
                                    from_email=settings.EMAIL_HOST_USER,
                                    html_message=create_email_template(
                                        template_name='transactions/emails/confirmation_code_email.html',
                                        context={
                                            'uuid': self.uuid,
                                            'current_site': current_site,
                                            'code': code
                                        }))
