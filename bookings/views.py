import logging

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from core.emailing import send_booking_notification
from core.permissions import IsStaffOnly, IsStaffOrReadOnly
from .models import Booking, Location
from .serializers import BookingSerializer, BookingStatusSerializer, LocationSerializer
from .services.google_calendar import create_booking_event, delete_booking_event

logger = logging.getLogger(__name__)


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsStaffOrReadOnly]


class BookingViewSet(viewsets.ModelViewSet):
    """
    POST is public (the booking form) — every other action is admin-only.

    Create flow, per the "save first, sync second" rule: the booking row is
    written to the database unconditionally, THEN we attempt a best-effort
    Google Calendar sync. A Calendar API failure is recorded on the row and
    logged, but the request still returns 201 to the customer — a Google
    outage must never look like a failed booking.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsStaffOnly()]

    def get_throttles(self):
        # Only the public create path needs the strict scope — staff
        # list/status-update/destroy actions stay on the general 'user' rate
        # (see settings.py) so admin panel use never gets throttled.
        if self.action == 'create':
            self.throttle_scope = 'public_write'
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def perform_create(self, serializer):
        # travel_fee is read-only on the serializer (see serializers.py) —
        # compute it here from the Location table instead of trusting
        # whatever the client sent. Free-text "Other" locations that don't
        # match a known Location row simply get 0; staff follow up manually,
        # matching the booking form's own "final pricing confirmed after
        # consultation" copy.
        location = Location.objects.filter(name__iexact=serializer.validated_data.get('location', '')).first()
        booking = serializer.save(travel_fee=location.travel_fee if location else 0)
        try:
            event_id, error = create_booking_event(booking)
        except Exception as exc:  # google_calendar already catches internally; this is a last-resort net
            event_id, error = None, str(exc)
        update_fields = []
        if event_id:
            booking.google_calendar_event_id = event_id
            update_fields.append('google_calendar_event_id')
        if error:
            booking.calendar_sync_error = error
            update_fields.append('calendar_sync_error')
        if update_fields:
            booking.save(update_fields=update_fields)

        try:
            email_error = send_booking_notification(booking)
            if email_error:
                logger.warning('Booking notification email failed for booking %s: %s', booking.pk, email_error)
        except Exception:  # emailing.py already catches internally; this is a last-resort net
            logger.exception('Booking notification email failed unexpectedly for booking %s', booking.pk)

    def perform_destroy(self, instance):
        if instance.google_calendar_event_id:
            delete_booking_event(instance.google_calendar_event_id)
        instance.delete()

    @action(detail=True, methods=['patch'], permission_classes=[IsStaffOnly])
    def set_status(self, request, pk=None):
        """PATCH /api/bookings/{id}/set_status/ {status: 'Contacted'} — the
        admin table's click-to-cycle status button."""
        booking = self.get_object()
        serializer = BookingStatusSerializer(booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(BookingSerializer(booking).data)
