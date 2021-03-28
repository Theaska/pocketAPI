from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication

from jwt_helper.exceptions import AuthenticationFailed, TokenException
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
            try:
                user = AccessToken.get_user_from_token(token)
            except TokenException as exc:
                raise AuthenticationFailed(str(exc))
            return user, token





