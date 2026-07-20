from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import add_log
from .models import ContactSubmission


@receiver(post_save, sender=ContactSubmission)
def log_contact_saved(sender, instance, created, **kwargs):
    if created:
        add_log('contact', f'New contact form submission from {instance.name or "a visitor"}')
