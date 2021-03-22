from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from rest_framework.authentication import BaseAuthentication

from .exceptions import AuthenticationFailed
from jwt_helper.token import AccessToken

User = get_user_model()


class JWTAuthentication(BaseAuthentication):
    def authenticate_header(self, request):
        return getattr(settings, 'AUTH_HEADER_NAME', 'access token')

    def authenticate(self, request):
        headers = request.headers
        auth_header_name = self.authenticate_header(request)
        token = headers.get(auth_header_name, '')
        if token:
            user = AccessToken.get_user_from_token(token)
            return user

    def get_user(self, token):
        """
            Get user id from token and return user object
        """
        user_id = token.get('user')
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExists():
            raise AuthenticationFailed(_('User not found'))
        else:
            if user.if_confirmed:
                return user
            else:
                raise AuthenticationFailed(_('User did not activate profile'))





