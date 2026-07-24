"""
One-off diagnostic command: verifies both mailboxes (hello@ for bookings,
noreply@ for admin-login alerts) actually authenticate and send.

Run via cPanel's "Setup Python App" -> "Execute python script" field:
    manage.py test_email

Sends two real emails to STUDIO_NOTIFICATION_EMAIL, clearly marked as tests.
"""
from datetime import date, time

from django.core.management.base import BaseCommand

from bookings.models import Booking
from core.emailing import send_admin_login_notification, send_booking_notification


class Command(BaseCommand):
    help = 'Sends test emails via both configured mailboxes (hello@ and noreply@).'

    def handle(self, *args, **options):
        test_booking = Booking(
            name='TEST EMAIL (safe to ignore)',
            gender='',
            email='test@example.com',
            country_code='+91',
            phone='0000000000',
            appointment_type='Studio Service',
            party_size='Single (1 person)',
            location='Law Gate',
            preferred_date=date.today(),
            preferred_time=time(14, 0),
            notes='Sent by manage.py test_email to verify hello@ SMTP credentials.',
            travel_fee=0,
        )
        booking_error = send_booking_notification(test_booking)
        if booking_error:
            self.stdout.write(self.style.ERROR(f'hello@ (booking notification) FAILED: {booking_error}'))
        else:
            self.stdout.write(self.style.SUCCESS('hello@ (booking notification) SUCCESS'))

        login_error = send_admin_login_notification('test-user', '0.0.0.0')
        if login_error:
            self.stdout.write(self.style.ERROR(f'noreply@ (admin login notification) FAILED: {login_error}'))
        else:
            self.stdout.write(self.style.SUCCESS('noreply@ (admin login notification) SUCCESS'))
