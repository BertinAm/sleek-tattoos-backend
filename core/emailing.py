"""
Outbound email via the studio's two real Namecheap-hosted mailboxes (SMTP,
cPanel mail on sleektattoos.com). Two separate sending identities, matching
two separate real mailboxes on the server, not just two different "From"
headers off one connection. SMTP requires authenticating as a real mailbox;
sending "From: noreply@..." while authenticated as hello@ would misalign
with SPF/DKIM checks on receiving servers and risks landing in spam, so
each purpose gets its own connection with its own credentials:

- hello@sleektattoos.com   -> booking notifications (bookings/views.py)
- noreply@sleektattoos.com -> system notifications, e.g. admin login alerts
  (core/views.py)

Every email is sent as HTML (templates in core/templates/emails/, styled to
match the site) with a plain-text fallback for clients that don't render
HTML. Both are "best effort", matching bookings/services/google_calendar.py's
philosophy: every function here swallows its own exceptions and returns an
error string (or None on success) rather than raising. An email provider
hiccup must never block a booking from saving or an admin from logging in.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


def _send(subject, text_body, html_body, from_email, username, password, reply_to=None, to=None) -> str | None:
    """`to` defaults to the studio's own inbox (every email until now only
    ever went there) — pass it explicitly to email an actual end user
    (a contact-form submitter, a newsletter subscriber)."""
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
            # Without this, a blocked/unreachable SMTP port hangs forever
            # instead of failing: smtplib's default socket timeout is None
            # (no timeout at all). 15s is generous for a same-host SMTP
            # handshake; if it can't connect by then, it's not going to.
            timeout=15,
        )
        message = EmailMultiAlternatives(
            subject=subject, body=text_body, from_email=from_email,
            to=to or [settings.STUDIO_NOTIFICATION_EMAIL], connection=connection,
            reply_to=[reply_to] if reply_to else None,
        )
        message.attach_alternative(html_body, 'text/html')
        message.send(fail_silently=False)
        return None
    except Exception as exc:
        logger.exception('Failed to send email from %s', from_email)
        return str(exc)


def send_booking_notification(booking) -> str | None:
    """Notifies the studio of a new booking request, from hello@. Reply-To
    is set to the customer's own email so replying goes straight to them."""
    subject = f'New booking request: {booking.name}'
    rows = [
        ('Name', booking.name),
        ('Gender', booking.gender or '-'),
        ('Email', booking.email),
        ('Phone', f'{booking.country_code} {booking.phone}'),
        ('Appointment type', booking.appointment_type),
        ('Party size', booking.party_size),
        ('Location', booking.location),
        ('Preferred date/time', f'{booking.preferred_date} {booking.preferred_time}'),
        ('Travel fee', f'Rs. {booking.travel_fee}'),
        ('Reference images', f'{len(booking.reference_images)} attached'),
    ]
    text_body = '\n'.join(f'{label}: {value}' for label, value in rows)
    if booking.notes:
        text_body += f'\n\nNotes: {booking.notes}'
    text_body += '\n\nView in the admin panel to update status.'

    html_body = render_to_string('emails/booking_notification.html', {'booking': booking, 'rows': rows})

    return _send(
        subject, text_body, html_body, settings.EMAIL_HOST_USER,
        settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD,
        reply_to=booking.email,
    )


def send_contact_notification(contact) -> str | None:
    """Notifies the studio of a new contact-form submission, from hello@.
    Reply-To is the customer's own email, mirroring send_booking_notification."""
    subject = f'New contact form submission: {contact.name}'
    text_body = (
        f'Name: {contact.name}\n'
        f'Email: {contact.email}\n'
        f'Phone: {contact.phone or "-"}\n\n'
        f'Message:\n{contact.message}\n\n'
        f'Reply from the admin panel to respond directly.'
    )
    html_body = render_to_string('emails/contact_notification.html', {'contact': contact})
    return _send(
        subject, text_body, html_body, settings.EMAIL_HOST_USER,
        settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD,
        reply_to=contact.email,
    )


def send_contact_reply(contact, reply_text) -> str | None:
    """Sends the admin's reply to whoever submitted the contact form, from
    hello@ — the address customers already know to reply to."""
    subject = f'Re: your message to Sleek Tattoos'
    text_body = f'{reply_text}\n\n---\nYour original message:\n{contact.message}'
    html_body = render_to_string('emails/contact_reply.html', {'contact': contact, 'reply_text': reply_text})
    return _send(
        subject, text_body, html_body, settings.EMAIL_HOST_USER,
        settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD,
        to=[contact.email],
    )


def send_admin_login_notification(username, ip_address=None) -> str | None:
    """Notifies the studio someone logged into the admin panel, from noreply@."""
    subject = f'Admin login: {username}'
    ts = timezone.now().strftime('%d %b %Y, %I:%M %p %Z').strip()

    text_body = f'{username} just logged into the Sleek Tattoos admin panel.\nTime: {ts}'
    if ip_address:
        text_body += f'\nIP address: {ip_address}'

    html_body = render_to_string('emails/admin_login_notification.html', {
        'username': username, 'ip_address': ip_address, 'timestamp': ts,
    })

    return _send(
        subject, text_body, html_body, settings.NOREPLY_EMAIL_HOST_USER,
        settings.NOREPLY_EMAIL_HOST_USER, settings.NOREPLY_EMAIL_HOST_PASSWORD,
    )
