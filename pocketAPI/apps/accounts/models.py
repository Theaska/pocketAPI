import hashlib

from django.contrib.auth.models import AbstractUser
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from accounts.helpers import generate_confirm_email_token
from email_helpers import create_email_template


class User(AbstractUser):
    """
        Custom user model with additional fields:
        token:                  email confirmation token
        refresh_token_hash:     refresh token hash for validating refresh token
        is_confirmed:           if user confirmed his email address
    """
    email = models.EmailField(_('email address'), unique=True)
    token = models.CharField(_('confirm token'), null=True, blank=True, max_length=256)
    refresh_token_hash = models.CharField(max_length=256, blank=True, null=True)
    is_confirmed = models.BooleanField(_('confirmed email'), default=False, help_text=_('True if user confirmed email'))

    def generate_and_set_confirm_token(self):
        token = generate_confirm_email_token(user=self, key=settings.SECRET_KEY)
        self.token = token.hexdigest()

    def set_refresh_token(self, token):
        self.refresh_token_hash = token.md5_hash.hexdigest()

    def send_confirmation_email(self):
        """
            Send email confirmation for user
        """
        current_site = Site.objects.get_current()
        self.email_user(subject=_('Confirm email from {domain}'.format(domain=current_site.domain)),
                        message='email confirmation',
                        from_email=settings.EMAIL_HOST_USER,
                        html_message=create_email_template(template_name='accounts/emails/confirm_email.html', context={
                            'user': self,
                            'current_site': current_site,
                        }))


    

