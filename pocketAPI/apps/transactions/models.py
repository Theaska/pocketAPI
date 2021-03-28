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
from .helpers import StatusMixin, TransactionStatus, ActionTransactions


class TransactionQuerySet(models.QuerySet):
    def visible(self):
        return self.filter(pocket__is_archived=False)

    def active(self):
        return self.visible().filter(Q(status=TransactionStatus.CREATED) | Q(status=TransactionStatus.IN_PROCESS))

    def created(self):
        return self.visible().filter(status=TransactionStatus.CREATED)

    def in_progress(self):
        return self.visible().filter(status=TransactionStatus.IN_PROCESS)

    def finished(self):
        return self.visible().filter(status=TransactionStatus.FINISHED)

    def cancelled(self):
        return self.visible().filter(status=TransactionStatus.CANCELLED)


class PocketTransaction(StatusMixin):
    """
        Model for pocket's transactions
    """
    pocket = models.ForeignKey(Pocket, verbose_name=_('Pocket'), on_delete=models.CASCADE, related_name='transactions')
    uuid = models.UUIDField(_('UUID'), default=uuid.uuid4, unique=True)
    sum = models.FloatField(_('sum'), validators=[MinValueValidator(0), MaxValueValidator(100000)])
    action = models.PositiveIntegerField(
        _('action'),
        choices=ActionTransactions.choices()
    )
    date_created = models.DateTimeField(_('date created'), auto_now_add=True)
    date_updated = models.DateTimeField(_('date updated'), auto_now=True)
    comment = models.TextField(_('comment'), blank=True, null=True)

    objects = TransactionQuerySet.as_manager()

    @transaction.atomic()
    def delete(self, using=None, keep_parents=False):
        """
            Delete transaction.
            If status of transaction is not cancelled, then trying to cancel transaction
            and only after success cancelling delete it.
        """
        if self.status != TransactionStatus.CANCELLED:
            self.cancel()
        super().delete(using, keep_parents)

    @property
    def action_name(self):
        return ActionTransactions.dict()[self.action]

    def activate(self):
        """
            Activate transaction. Refill or debit pocket with transaction sum and set status as FINISHED.
            Can activate ONLY Confirmed transaction for non archived pocket.
        """
        if self.status == TransactionStatus.FINISHED:
            raise TransactionError('This transaction has finished already')

        if self.status != TransactionStatus.CONFIRMED:
            raise TransactionError(
                'Can activate transaction only with status {}'.format(TransactionStatus.CONFIRMED.name)
            )
        elif self.pocket.is_archived:
            raise TransactionError('Can not activate transaction for archived pocket')

        try:
            if self.action == ActionTransactions.DEBIT:
                self.pocket.debit(self.sum)
            elif self.action == ActionTransactions.REFILL:
                self.pocket.refill(self.sum)
        except Exception as exc:
            self.set_cancelled()
            self.save()
            raise TransactionError(str(exc))
        else:
            self.pocket.save()
            self.set_finished()
            self.save()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.pocket.is_archived:
            raise TransactionError('Can not create transaction for archived pocket')
        super().save(force_insert, force_update, using, update_fields)

    @transaction.atomic()
    def refund(self):
        """
            Refund money from transaction.
            If action was DEBIT then refill money.
            If action was REFILL then debit money.
            If pocket balance less than debit money, then raise TransactionError.
        """
        if self.action == ActionTransactions.DEBIT:
            self.pocket.refill(self.sum)
            self.pocket.save()
        elif self.action == ActionTransactions.REFILL:
            try:
                self.pocket.debit(self.sum)
                self.pocket.save()
            except ValueError:
                raise TransactionError('Not enough money for refund')

    @transaction.atomic()
    def cancel(self):
        """
            Cancel transaction.
            If status of transaction is finished, then need to try to refund money (or refill).
        """
        if self.status == TransactionStatus.FINISHED:
            self.refund()
        if self.status == TransactionStatus.CANCELLED:
            raise TransactionError('Transaction has already cancelled')
        self.set_cancelled()
        self.save()

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
