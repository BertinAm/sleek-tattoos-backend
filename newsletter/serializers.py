from rest_framework import serializers

from .models import Subscriber


class SubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscriber
        fields = ['id', 'email', 'name', 'is_active', 'subscribed_at', 'unsubscribed_at']
        read_only_fields = fields


class SubscribeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    name = serializers.CharField(max_length=160, required=False, allow_blank=True, default='')
