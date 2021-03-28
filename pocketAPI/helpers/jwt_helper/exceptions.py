from rest_framework import status
from rest_framework.exceptions import APIException


class TokenException(Exception):
    pass


class AuthenticationFailed(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Invalid Token'
