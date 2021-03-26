from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, mixins
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from serializers_helpers import MessageSerializer
from .conf import VALIDATION_CODE_LENGTH
from .helpers import generate_code, save_deletion_pocket_code
from .models import Pocket
from .serializers import PocketSerializer, ConfirmDeletionSerializer
import pocket.permissions as pocket_permissions


class PocketAPIView(ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, pocket_permissions.IsOwner]
    serializer_class = PocketSerializer
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    def get_serializer_class(self):
        if self.action == 'destroy':
            return ConfirmDeletionSerializer
        else:
            return super().get_serializer_class()

    def get_queryset(self):
        return Pocket.objects.active().filter(user=self.request.user)

    @swagger_auto_schema(request_body=ConfirmDeletionSerializer())
    def destroy(self, request, *args, **kwargs):
        return super(PocketAPIView, self).destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        pocket = self.get_object()
        pocket.delete()


class SendConfirmationDeleteCode(APIView):
    permission_classes = [permissions.IsAuthenticated, pocket_permissions.IsOwner]
    serializer_class = MessageSerializer

    def get_queryset(self):
        return Pocket.objects.active().filter(user=self.request.user)

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), uuid=self.kwargs['uuid'])
        return obj

    def get(self, request, uuid):
        # send confirmation code for confirm deletion
        instance = self.get_object()
        confirmation_code = generate_code(length=VALIDATION_CODE_LENGTH)
        instance.send_confirmation_delete_code(confirmation_code)
        save_deletion_pocket_code(pocket_uuid=instance.uuid, code=confirmation_code)
        return Response({'message': "We sent confirmation code to your email"})

