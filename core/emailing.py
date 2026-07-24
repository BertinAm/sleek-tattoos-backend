"""
Outbound email via the studio's two real Namecheap-hosted mailboxes (SMTP,
cPanel mail on sleektattoos.com). Two separate sending identities, matching
two separate real mailboxes on the server — not just two different "From"
headers off one connection. SMTP requires authenticating as a real mailbox;
sending "From: noreply@..." while authenticated as hello@ would misalign
with SPF/DKIM checks on receiving servers and risks landing in spam, so
each purpose gets its own connection with its own credentials:

- hello@sleektattoos.com   -> booking notifications (bookings/views.py)
- noreply@sleektattoos.com -> system notifications, e.g. admin login alerts
  (core/views.py)

Both are "best effort", matching bookings/services/google_calendar.py's
philosophy: every function here swallows its own exceptions and returns an
error string (or None on success) rather than raising. An email provider
hiccup must never block a booking from saving or an admin from logging in.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMessage, get_connection

logger = logging.getLogger(__name__)


def _send(subject, body, from_email, username, password, reply_to=None) -> str | None:
    if not password:
        return f'No password configured for {username} (EMAIL env vars not set).'
    try:
        connection = get_connection(
            backend=settings.EMAIL_BACKEND,
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=username,
            password=password,
            use_ssl=settings.EMAIL_USE_SSL,
            use_tls=settings.EMAIL_USE_TLS,
        )
        message = EmailMessage(
            subject=subject, body=body, from_email=from_email,
            to=[settings.STUDIO_NOTIFICATION_EMAIL], connection=connection,
            reply_to=[reply_to] if reply_to else None,
        )
        message.send(fail_silently=False)
        return None
    except Exception as exc:
        logger.exception('Failed to send email from %s', from_email)
        return str(exc)


def send_booking_notification(booking) -> str | None:
    """Notifies the studio of a new booking request, from hello@. Reply-To
    is set to the customer's own email so replying goes straight to them."""
    subject = f'New booking request — {booking.name}'
    body = (
        f'Name: {booking.name}\n'
        f'Gender: {booking.gender or "-"}\n'
        f'Email: {booking.email}\n'
        f'Phone: {booking.country_code} {booking.phone}\n'
        f'Appointment type: {booking.appointment_type}\n'
        f'Party size: {booking.party_size}\n'
        f'Location: {booking.location}\n'
        f'Preferred date/time: {booking.preferred_date} {booking.preferred_time}\n'
        f'Travel fee: Rs. {booking.travel_fee}\n'
        f'Notes: {booking.notes or "-"}\n'
        f'Reference images: {len(booking.reference_images)} attached\n\n'
        f'View in the admin panel to update status.'
    )
    return _send(
        subject, body, settings.EMAIL_HOST_USER,
        settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD,
        reply_to=booking.email,
    )


def send_admin_login_notification(username, ip_address=None) -> str | None:
    """Notifies the studio someone logged into the admin panel, from noreply@."""
    subject = f'Admin login: {username}'
    body = f'{username} just logged into the Sleek Tattoos admin panel.'
    if ip_address:
        body += f'\nIP address: {ip_address}'
    return _send(
        subject, body, settings.NOREPLY_EMAIL_HOST_USER,
        settings.NOREPLY_EMAIL_HOST_USER, settings.NOREPLY_EMAIL_HOST_PASSWORD,
    )
