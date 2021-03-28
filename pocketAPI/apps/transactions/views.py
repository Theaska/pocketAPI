import coreschema
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, mixins, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from django.conf import settings

from pocket.helpers import generate_code
from serializers_helpers import MessageSerializer
from transactions.exceptions import TransactionError
from transactions.helpers import save_confirmation_transaction_code
from transactions.models import PocketTransaction, TransactionStatus
from transactions.serializers import TransactionSerializer, ConfirmTransactionSerializer
import transactions.permissions as transaction_permissions


class TransactionViewSet(mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.DestroyModelMixin,
                         mixins.ListModelMixin,
                         GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, ]
    serializer_class = TransactionSerializer
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'
    filter_fields = {
        'pocket__uuid': {
            'description': 'uuid of pocket',
            'schema': coreschema.String(
                    pattern=r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}'
                )
        },
    }

    def get_queryset(self):
        queryset = PocketTransaction.objects.visible().filter(pocket__user=self.request.user)
        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except TransactionError as te:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'errors': [str(te), ]})
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConfirmTransaction(GenericAPIView):
    """
        Confirm transaction with confirmation code from email.
    """
    serializer_class = ConfirmTransactionSerializer
    permission_classes = [permissions.IsAuthenticated, transaction_permissions.IsOwner]
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    def get_queryset(self):
        return PocketTransaction.objects.active()

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    @swagger_auto_schema(responses={200: MessageSerializer()})
    def post(self, request, uuid):
        transaction = self.get_object()
        serializer = self.get_serializer(data=request.data, transaction=transaction)
        if serializer.is_valid(raise_exception=True):
            try:
                transaction.activate()
            except TransactionError as er:
                transaction.cancel()
                return Response({'error': str(er)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                message = MessageSerializer({'message': 'Your transaction have confirmed'})
                return Response(message.data)


class SendConfirmationCode(GenericAPIView):
    """
        Send code to user email for confirm transaction.
    """
    permission_classes = [permissions.IsAuthenticated, transaction_permissions.IsOwner]
    serializer_class = MessageSerializer
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    def get_queryset(self):
        return PocketTransaction.objects.active()

    def get(self, request, uuid):
        # send confirmation code for confirm transaction
        instance = self.get_object()
        confirmation_code = generate_code(length=settings.VALIDATION_CODE_LENGTH)
        save_confirmation_transaction_code(transaction_uuid=instance.uuid, code=confirmation_code)
        instance.send_confirmation_code(confirmation_code)
        instance.change_status(TransactionStatus.IN_PROCESS)
        message = self.serializer_class({'message': "We sent confirmation code to your email"})
        return Response(message.data)
