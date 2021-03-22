from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from jwt_helper.serializers import JWTSerializer, UpdateTokensSerializer


class UpdateTokensView(APIView):
    serializer_class = UpdateTokensSerializer

    def get_serializer(self):
        return self.serializer_class()

    @swagger_auto_schema(
        operation_description='Update jwt tokens using refresh token',
        responses={200: JWTSerializer()}
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            return Response(serializer.validated_data)
