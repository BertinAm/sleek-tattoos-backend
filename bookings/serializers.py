from rest_framework import serializers

from .models import Booking, Location


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'travel_fee', 'order']


class BookingSerializer(serializers.ModelSerializer):
    # Booking.notes is an unbounded TextField at the DB layer; cap it here so
    # the public, unauthenticated create endpoint can't be used to stuff
    # arbitrarily large payloads into the database.
    notes = serializers.CharField(max_length=2000, required=False, allow_blank=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'name', 'gender', 'email', 'country_code', 'phone', 'appointment_type', 'party_size',
            'location', 'preferred_date', 'preferred_time', 'notes', 'reference_images', 'travel_fee',
            'status', 'google_calendar_event_id', 'calendar_sync_error', 'created_at',
        ]
        # travel_fee is intentionally read-only here even though it's a
        # "real" field on create: it's computed server-side from the
        # Location table in BookingViewSet.perform_create, never trusted
        # from client input — otherwise any anonymous POST could set its own
        # (fake) travel fee.
        read_only_fields = ['status', 'google_calendar_event_id', 'calendar_sync_error', 'created_at', 'travel_fee']

    def validate_reference_images(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Must be a list of image URLs.')
        if len(value) > 10:
            raise serializers.ValidationError('Maximum 10 reference images.')
        for url in value:
            if not isinstance(url, str) or not url or len(url) > 500:
                raise serializers.ValidationError('Each reference image must be a URL string under 500 characters.')
        return value


class BookingStatusSerializer(serializers.ModelSerializer):
    """Used by the admin panel's status-cycle button — only `status` is writable there."""

    class Meta:
        model = Booking
        fields = ['status']
