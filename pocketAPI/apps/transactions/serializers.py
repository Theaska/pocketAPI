from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from transactions.helpers import get_confirmation_transaction_code
from transactions.models import PocketTransaction, ActionTransactions


class TransactionSerializer(serializers.ModelSerializer):
    """
        Serializer for get/create new transactions.
    """
    status = serializers.SerializerMethodField()
    uuid = serializers.UUIDField(read_only=True)
    action = serializers.ChoiceField(choices=ActionTransactions.choices(), default=ActionTransactions.REFILL,
                                     help_text=str(ActionTransactions.choices()))
    action_name = serializers.SerializerMethodField()

    def get_action_name(self, obj):
        return obj.action_name

    def get_status(self, obj):
        return obj.status_name

    def validate_pocket(self, pocket):
        if pocket.is_archived:
            raise ValidationError('Pocket does not exists')
        else:
            return pocket

    def validate(self, attrs):
        if attrs['action'] == ActionTransactions.DEBIT:
            pocket = attrs['pocket']
            if pocket.balance < attrs['sum']:
                raise ValidationError('Not enough money on pocket balance for creating transaction')
        return attrs

    class Meta:
        model = PocketTransaction
        fields = ('id', 'uuid', 'sum', 'action', 'action_name', 'date_created',
                  'date_updated', 'comment', 'status', 'pocket')


class ConfirmTransactionSerializer(serializers.Serializer):
    """
        Serializer for confirm transaction with code.
    """
    code = serializers.CharField()

    def __init__(self, transaction=None, *args, **kwargs):
        self.transaction = transaction
        super().__init__(*args, **kwargs)

    def validate_code(self, value: str):
        if not value.isnumeric():
            raise ValidationError('Code must be numeric')
        else:
            return value

    def validate(self, attrs):
        if not self.transaction:
            raise ValidationError('transaction is none')

        code = get_confirmation_transaction_code(self.transaction.uuid)
        if not code == attrs['code']:
            raise ValidationError('Invalid code')
        else:
            self.transaction.set_confirmed()
        return attrs
