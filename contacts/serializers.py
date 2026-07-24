from rest_framework import serializers

from .models import ContactSubmission


class ContactSubmissionSerializer(serializers.ModelSerializer):
    # message is an unbounded TextField at the DB layer; cap it here since
    # this is a public, unauthenticated create endpoint.
    message = serializers.CharField(max_length=5000)

    class Meta:
        model = ContactSubmission
        fields = ['id', 'name', 'email', 'phone', 'message', 'created_at', 'replied_at', 'reply_text']
        read_only_fields = ['created_at', 'replied_at', 'reply_text']


class ContactReplySerializer(serializers.Serializer):
    message = serializers.CharField(max_length=5000)
