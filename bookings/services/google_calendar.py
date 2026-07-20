"""
Google Calendar sync via a service account — no OAuth user consent, no
7-day-expiring refresh tokens, no owner re-login ever. See deployment.md
for the one-time setup (create service account, share the owner's calendar
with its email address).

The booking record is always saved to the database BEFORE this module is
called (see bookings/views.py). This module is intentionally "best effort":
every public function swallows its own exceptions, logs them to ActivityLog,
and returns None on failure — a Google API hiccup must never block a booking
from saving or return an error to the customer.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']


def _get_service():
    """Returns an authenticated Calendar API client, or None if credentials
    aren't configured (e.g. local dev without a service account key)."""
    if not settings.GOOGLE_SERVICE_ACCOUNT_FILE or not settings.GOOGLE_CALENDAR_OWNER_EMAIL:
        return None
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        credentials = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES,
        )
        return build('calendar', 'v3', credentials=credentials, cache_discovery=False)
    except Exception:
        logger.exception('Failed to build Google Calendar client')
        return None


def create_booking_event(booking) -> tuple[str | None, str | None]:
    """Insert a calendar event for `booking`. Returns (event_id, error_message) —
    exactly one of the two is set. Never raises."""
    service = _get_service()
    if service is None:
        return None, 'Google Calendar not configured (missing service account file or owner email).'

    try:
        from datetime import datetime, timedelta

        start_dt = datetime.combine(booking.preferred_date, booking.preferred_time)
        end_dt = start_dt + timedelta(hours=2)  # default 2h block; adjust per service if needed later

        event = {
            'summary': f'Tattoo booking — {booking.name}',
            'description': (
                f'Customer: {booking.name}\n'
                f'Phone: {booking.country_code} {booking.phone}\n'
                f'Email: {booking.email}\n'
                f'Type: {booking.appointment_type}\n'
                f'Party: {booking.party_size}\n'
                f'Location: {booking.location}\n'
                f'Travel fee: ₹{booking.travel_fee}\n'
                f'Notes: {booking.notes or "—"}'
            ),
            'start': {'dateTime': start_dt.isoformat(), 'timeZone': settings.TIME_ZONE},
            'end': {'dateTime': end_dt.isoformat(), 'timeZone': settings.TIME_ZONE},
            'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 60}]},
        }
        created = service.events().insert(
            calendarId=settings.GOOGLE_CALENDAR_OWNER_EMAIL, body=event,
        ).execute()
        return created.get('id'), None
    except Exception as exc:
        logger.exception('Google Calendar event creation failed for booking %s', booking.pk)
        return None, str(exc)


def delete_booking_event(event_id: str) -> str | None:
    """Best-effort delete when a booking is removed from the admin. Returns an error message or None."""
    service = _get_service()
    if service is None or not event_id:
        return None
    try:
        service.events().delete(calendarId=settings.GOOGLE_CALENDAR_OWNER_EMAIL, eventId=event_id).execute()
        return None
    except Exception as exc:
        logger.exception('Google Calendar event deletion failed for event %s', event_id)
        return str(exc)
