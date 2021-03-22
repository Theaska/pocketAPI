import hashlib

from django.utils import timezone


def generate_confirm_email_token(user, key):
    """
        Generate token for confirmation email for user
    """
    string = f'{user.email}{user.username}{user.password}{key}{timezone.now().timestamp}'
    return hashlib.sha256(string.encode('utf-8'))

