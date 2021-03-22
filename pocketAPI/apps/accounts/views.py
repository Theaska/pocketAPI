from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializer import UserSerializer, EmailTokenSerializer, ResendEmailTokenSerializer
from jwt_helper.serializers import JWTSerializer, AuthenticateUserToken
from serializers_helpers import MessageSerializer


class CreateUserView(CreateAPIView):
    """
        Create new user
    """
    serializer_class = UserSerializer


class LoginView(APIView):
    """
        Login and get access and refresh tokens
    """
    serializer_class = AuthenticateUserToken

    def get_serializer(self):
        return self.serializer_class()

    @swagger_auto_schema(responses={200: JWTSerializer()})
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            return Response(serializer.validated_data)


class SendEmailToken(APIView):
    """
        Send confirmation email again
    """
    serializer_class = ResendEmailTokenSerializer

    def get_serializer(self):
        return self.serializer_class()

    @swagger_auto_schema(responses={200: MessageSerializer()})
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            return Response(serializer.validated_data)


class ConfirmEmailView(APIView):
    """
        Confirm email address
    """
    serializer_class = EmailTokenSerializer

    def get_serializer(self):
        return self.serializer_class()

    @swagger_auto_schema(responses={200: MessageSerializer()})
    def get(self, request, **kwargs):
        serializer = self.serializer_class(data={'token': kwargs['token']})
        if serializer.is_valid(raise_exception=True):
            return Response(serializer.validated_data)


