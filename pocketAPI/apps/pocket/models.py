from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.db import models
import uuid
from django.utils.translation import ugettext_lazy as _

from email_helpers import create_email_template

UserModel = get_user_model()


class PocketManager(models.QuerySet):
    def active(self):
        return self.filter(is_archived=False)

    def archived(self):
        return self.filter(is_archived=True)

    def delete(self):
        self.update(is_archived=True)

    def hard_delete(self):
        return super(PocketManager, self).delete()


class Pocket(models.Model):
    user = models.ForeignKey(UserModel, related_name='pockets', on_delete=models.CASCADE, db_index=True,)
    uuid = models.UUIDField(unique=True, db_index=True, editable=False, default=uuid.uuid4)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    name = models.CharField(_('name of pocket'), max_length=128)
    description = models.TextField(_('description of pocket'), max_length=512, blank=True, null=True)

    # we will not delete pockets, just put them to archive
    is_archived = models.BooleanField(_('in archive'), default=False)

    objects = PocketManager.as_manager()

    class Meta:
        verbose_name = _('Pocket')
        verbose_name_plural = _('Pockets')

    def send_confirmation_delete_code(self, code):
        """
            Send confirmation code for deleting pocket
        """
        current_site = Site.objects.get_current()
        self.user.email_user(fail_silently=True,
                             subject=_('Confirm deletion pocket in {domain}'.format(domain=current_site.domain)),
                             message='email confirmation',
                             from_email=settings.EMAIL_HOST_USER,
                             html_message=create_email_template(
                                 template_name='pocket/emails/confirmation_code_email.html',
                                 context={
                                     'uuid': self.uuid,
                                     'current_site': current_site,
                                     'code': code
                                 }))

    def delete(self, using=None, keep_parents=False):
        self.is_archived = True
        self.save()
