import binascii
import hashlib
import base64
from typing import Dict, Union

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
import jwt

from .exceptions import TokenException

UserModel = get_user_model()

ALGORITHMS = (
    "HS256",
    "HS384",
    "HS512",
    "PS256",
    "PS384",
    "PS512",
    "RS256",
    "RS384",
    "RS512",
    "ES256",
    "ES256K",
    "ES384",
    "ES512",
    "EdDSA",
)


class Token:
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return str(self.value)

    @property
    def value(self):
        return self._value

    @property
    def md5_hash(self):
        return hashlib.md5(self._value.encode('utf-8'))

    @property
    def b64_encoded(self):
        return base64.b64encode(self._value.encode("utf-8"))


class TokenGenerator:
    """
        Base class for creating JSON Web Token.
        algorithm:      algorithm which will be used for encoding token
        lifetime:       how many seconds token will be valid
    """
    TOKEN_CLASS = Token

    def __init__(self, algorithm: str = 'HS256', lifetime: int = 60 * 60):
        self.lifetime = lifetime
        self._validate_algorithm(algorithm)
        self.algorithm = algorithm

    def _validate_algorithm(self, algorithm: str):
        """ Check if algorithm is valid """
        if algorithm not in ALGORITHMS:
            raise TokenException('algorithm {} is not valid'.format(algorithm))

    def decode_token(self, token: str) -> Dict[str, any]:
        return jwt.decode(token, key=settings.SECRET_KEY, algorithms=(self.algorithm,))

    def get_payload(self) -> Dict[str, any]:
        return {
            'expired_time': (timezone.now() + timezone.timedelta(seconds=self.lifetime)).timestamp()
        }

    def generate_token(self):
        token = jwt.encode(payload=self.get_payload(), key=settings.SECRET_KEY, algorithm=self.algorithm)
        return self.TOKEN_CLASS(token)


class UserTokenGenerator(TokenGenerator):
    """ Token generator for creating token with user info """
    def __init__(self, user_id: str or int, username: str, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.username = username

    def get_payload(self) -> dict:
        payload = super(UserTokenGenerator, self).get_payload()
        payload.update({
            'user_id': self.user_id,
            'username': self.username
        })
        return payload


class AccessToken:
    """ Access Token for authenticate user """
    lifetime = getattr(settings, 'ACCESS_TOKEN_LIFETIME', 60*60*3)

    @classmethod
    def for_user(cls, user: UserModel) -> Token:
        """ Generate token for user with info: user_id and username """
        generator = UserTokenGenerator(user_id=user.id, username=user.username, lifetime=cls.lifetime)
        return generator.generate_token()

    @classmethod
    def get_user_from_token(cls, token: str) -> Union[UserModel, None]:
        """
            Return user from base64 encoded token and encoded token.
            Raises TokenException if token invalid.
        """
        try:
            token = base64.b64decode(token).decode()
        except binascii.Error:
            raise TokenException('Can not decode token')

        token = TokenGenerator().decode_token(token)

        if token['expired_time'] < timezone.now().timestamp():
            raise TokenException('Lifetime of token expired')

        user_id, username = token.get('user_id'), token.get('username')

        if user_id and username:
            try:
                user = UserModel.objects.get(username=username, id=user_id)
            except UserModel.DoesNotExist:
                raise TokenException('Invalid token')
            else:
                return user
        else:
            raise TokenException('Token does not provide user info')


class RefreshToken(AccessToken):
    """ Refresh Token for updating access and refresh tokens """
    lifetime = getattr(settings, 'REFRESH_TOKEN_LIFETIME', 60*60*3)

    @classmethod
    def for_user(cls, user: UserModel) -> Token:
        token = super().for_user(user)
        user.set_refresh_token(token)
        user.save()
        return token

    @classmethod
    def get_user_from_token(cls, token: str) -> Union[UserModel, None]:
        """
            Return user from base64 encoded token and encoded token.
            Raises TokenException if token invalid.
        """
        user = super().get_user_from_token(token)
        token = base64.b64decode(token.encode('utf-8'))
        if hashlib.md5(token).hexdigest() != user.refresh_token_hash:
            raise TokenException('Refresh token invalid')
        return user

