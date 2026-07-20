from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from core.models import add_log
from .models import Booking


@receiver(post_save, sender=Booking)
def log_booking_saved(sender, instance, created, **kwargs):
    if created:
        add_log('booking', f'New booking request from {instance.name or "a customer"}')
    else:
        add_log('booking', f'Updated booking {instance.pk} (status: {instance.status})')


@receiver(post_delete, sender=Booking)
def log_booking_deleted(sender, instance, **kwargs):
    add_log('booking', f'Deleted booking request ({instance.pk})')
