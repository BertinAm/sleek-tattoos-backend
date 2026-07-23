"""
One-off diagnostic command: verifies the Google Calendar service account is
configured correctly and can actually create an event — without touching the
booking database at all (uses an unsaved, in-memory Booking instance, never
calls .save()).

Run via cPanel's "Setup Python App" -> "Execute python script" field:
    manage.py test_calendar_sync

Safe to run repeatedly. Creates one throwaway calendar event per run, titled
"Tattoo booking — TEST BOOKING (safe to delete)" — deliberately not deleted
automatically, so you can visually confirm it actually shows up on the real
calendar. Delete it yourself from the calendar once confirmed.
"""
from datetime import date, time, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand

from bookings.models import Booking
from bookings.services.google_calendar import create_booking_event


class Command(BaseCommand):
    help = 'Creates a throwaway test event via the configured Google Calendar service account.'

    def handle(self, *args, **options):
        if not settings.GOOGLE_SERVICE_ACCOUNT_FILE:
            self.stdout.write(self.style.ERROR('GOOGLE_SERVICE_ACCOUNT_FILE is not set.'))
            return
        if not settings.GOOGLE_CALENDAR_OWNER_EMAIL:
            self.stdout.write(self.style.ERROR('GOOGLE_CALENDAR_OWNER_EMAIL is not set.'))
            return

        self.stdout.write(f'GOOGLE_SERVICE_ACCOUNT_FILE = {settings.GOOGLE_SERVICE_ACCOUNT_FILE}')
        self.stdout.write(f'GOOGLE_CALENDAR_OWNER_EMAIL = {settings.GOOGLE_CALENDAR_OWNER_EMAIL}')

        test_booking = Booking(
            name='TEST BOOKING (safe to delete)',
            gender='',
            email='test@example.com',
            country_code='+91',
            phone='0000000000',
            appointment_type='Studio Service',
            party_size='Single (1 person)',
            location='Law Gate',
            preferred_date=date.today() + timedelta(days=1),
            preferred_time=time(14, 0),
            notes='Created by manage.py test_calendar_sync to verify Google Calendar sync. Safe to delete.',
            travel_fee=0,
        )

        event_id, error = create_booking_event(test_booking)

        if error:
            self.stdout.write(self.style.ERROR(f'FAILED: {error}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'SUCCESS — event created with id: {event_id}'))
            self.stdout.write(
                'Check the owner calendar for "Tattoo booking — TEST BOOKING (safe to delete)" '
                'tomorrow at 2:00 PM. Delete it once confirmed.'
            )
