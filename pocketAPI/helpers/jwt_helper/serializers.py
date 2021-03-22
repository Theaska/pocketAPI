from __future__ import annotations

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from jwt_helper.exceptions import TokenException
from jwt_helper.token import AccessToken, RefreshToken, Token, TokenGenerator, UserTokenGenerator


class JWTSerializer(serializers.Serializer):
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    @classmethod
    def for_user(cls, user) -> JWTSerializer:
        """
            Get serializer with jwt tokens for user
            user:   current user model
        """
        access_token = AccessToken.for_user(user).b64_encoded
        refresh_token = RefreshToken.for_user(user).b64_encoded
        return cls({'access_token': access_token.decode(),
                    'refresh_token': refresh_token.decode()})


class AuthenticateUserToken(serializers.Serializer):
    """
        Serializer for authenticate user and get him access and refresh tokens.
    """
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        login = attrs['username']
        password = attrs['password']
        user = authenticate(username=login, password=password)
        if user:
            if user.is_confirmed:
                return JWTSerializer.for_user(user).data
            else:
                raise ValidationError('User is inactive. Please, check your email and activate your profile')
        else:
            raise ValidationError('Invalid password or login')


class UpdateTokensSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate(self, attrs):
        token = attrs['refresh_token']
        try:
            user = RefreshToken.get_user_from_token(token)
        except TokenException as te:
            raise ValidationError(str(te))
        return JWTSerializer.for_user(user).data


