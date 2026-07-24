from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import add_log
from .models import Subscriber


@receiver(post_save, sender=Subscriber)
def log_subscriber_created(sender, instance, created, **kwargs):
    if created:
        add_log('newsletter', f'New newsletter subscriber: {instance.email}')
