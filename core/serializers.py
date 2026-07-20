from django.contrib.auth.models import User
from rest_framework import serializers

from .models import ActivityLog


class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = ['id', 'type', 'message', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']


class ImageUploadSerializer(serializers.Serializer):
    MAX_SIZE = 5 * 1024 * 1024  # 5MB

    # ImageField already verifies (via Pillow) that the upload is a real,
    # openable image — not just a file with an image-sounding name/extension
    # — before it ever gets close to disk.
    file = serializers.ImageField()

    def validate_file(self, value):
        if value.size > self.MAX_SIZE:
            raise serializers.ValidationError('Image must be 5MB or smaller.')
        return value
