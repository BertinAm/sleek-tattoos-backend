from rest_framework import serializers

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'sender', 'text', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'visitor_token', 'name', 'unread', 'created_at', 'last_message_at', 'messages']


class ConversationListSerializer(serializers.ModelSerializer):
    """Lighter shape for the admin inbox list (no full message history)."""
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'name', 'unread', 'last_message_at', 'last_message']

    def get_last_message(self, obj):
        last = obj.messages.last()
        return last.text if last else ''


class SendMessageSerializer(serializers.Serializer):
    # Unbounded input here would let an anonymous visitor stuff arbitrarily
    # large payloads into Message.text (also a TextField with no DB-level cap).
    text = serializers.CharField(max_length=2000)
