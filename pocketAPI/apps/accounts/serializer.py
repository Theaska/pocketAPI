from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from serializers_helpers import MessageSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
        Serializer for creating new user
    """

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def create(self, validated_data):
        user = User(username=validated_data['username'], email=validated_data['email'])
        user.set_password(validated_data['password'])
        user.generate_and_set_confirm_token()
        user.save()
        user.send_confirmation_email()
        return user


class ResendEmailTokenSerializer(serializers.Serializer):
    """
        Serializer for resending email confirmation token
    """
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if user and not user.is_confirmed:
            user.generate_and_set_confirm_token()
            user.save()
            user.send_confirmation_email()
            return MessageSerializer({
                'message': 'We sent email to confirm your email address. Check your email {}'.format(user.email)
            }).data
        elif not user:
            raise ValidationError('Invalid login and password')
        else:
            raise ValidationError('You have already confirmed your email address')


class EmailTokenSerializer(serializers.Serializer):
    """
        Serializer for confirm email with token
    """
    token = serializers.CharField()

    def validate(self, attrs):
        token = attrs['token']
        try:
            user = User.objects.get(token=token)
            if not user.is_confirmed:
                user.is_confirmed = True
                user.save()
            else:
                raise ValidationError('You have already confirmed your profile.')
        except User.DoesNotExist:
            raise ValidationError('Invalid token')
        return MessageSerializer({"message": 'You have confirmed your profile successfully.'}).data
