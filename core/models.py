from django.db import models


class ActivityLog(models.Model):
    """Mirrors the frontend prototype's addLog() calls — one row per admin
    mutation across every app, so /api/logs/ can power the Activity Logs
    admin page exactly like lib/store.js used to."""

    TYPE_CHOICES = [
        ('news', 'News'),
        ('gallery', 'Gallery'),
        ('artists', 'Artists'),
        ('services', 'Services'),
        ('about', 'About'),
        ('booking', 'Booking'),
        ('support', 'Support'),
        ('contact', 'Contact'),
        ('newsletter', 'Newsletter'),
        ('auth', 'Auth'),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.type}] {self.message}'


def add_log(log_type: str, message: str) -> None:
    """Shared helper every app's signals call — keeps ActivityLog writes in one place."""
    ActivityLog.objects.create(type=log_type, message=message)
