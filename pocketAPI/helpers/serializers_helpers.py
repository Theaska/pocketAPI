from rest_framework import serializers


class MessageSerializer(serializers.Serializer):
    """
        Serializer for message response for swagger auto schema
    """
    message = serializers.CharField()