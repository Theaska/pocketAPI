from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .helpers import get_deletion_pocket_code
from .models import Pocket
from .conf import VALIDATION_CODE_LENGTH


class PocketSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    uuid = serializers.UUIDField(read_only=True)

    class Meta:
        model = Pocket
        fields = ('id', 'uuid', 'name', 'description', 'user')


class ConfirmDeletionSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=VALIDATION_CODE_LENGTH, max_length=VALIDATION_CODE_LENGTH)

    def __init__(self, pocket=None, *args, **kwargs):
        self.pocket = pocket
        super().__init__(*args, **kwargs)

    def validate_code(self, value: str):
        if not value.isnumeric():
            raise ValidationError('Code must be numeric')
        else:
            return value

    def validate(self, attrs):
        if not self.pocket:
            raise ValidationError('pocket is None')
        code = get_deletion_pocket_code(self.pocket.uuid)
        if not code == attrs['code']:
            raise ValidationError('Invalid code')
        return attrs


