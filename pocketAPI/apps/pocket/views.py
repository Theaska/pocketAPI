from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from serializers_helpers import MessageSerializer
from transactions.serializers import TransactionSerializer
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
        serializer = self.get_serializer(data=self.request.data, pocket=pocket)
        if serializer.is_valid(raise_exception=True):
            pocket.delete()


# class PocketTransaction(GenericAPIView):
#     """
#         Get transaction for pocket with uuid.
#     """
#     permission_classes = [permissions.IsAuthenticated, pocket_permissions.IsOwner]
#     lookup_field = 'uuid'
#     lookup_url_kwarg = 'uuid'
#     serializer_class = TransactionSerializer
#
#     def get_queryset(self):
#         return Pocket.objects.active().filter(user=self.request.user)
#
#     def get(self, request, uuid):
#         pocket = self.get_object()
#         serializer = self.get_serializer(pocket.transactions, many=True)
#         return Response(serializer.data)


class SendConfirmationDeleteCode(GenericAPIView):
    """
        Send code for confirm deleting pocket with uuid.
    """
    permission_classes = [permissions.IsAuthenticated, pocket_permissions.IsOwner]
    serializer_class = MessageSerializer
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    def get_queryset(self):
        return Pocket.objects.active()

    def get(self, request, uuid):
        # send confirmation code for confirm deletion
        instance = self.get_object()
        confirmation_code = generate_code(length=settings.VALIDATION_CODE_LENGTH)
        save_deletion_pocket_code(pocket_uuid=instance.uuid, code=confirmation_code)
        instance.send_confirmation_delete_code(confirmation_code)
        return Response({'message': "We sent confirmation code to your email"})

