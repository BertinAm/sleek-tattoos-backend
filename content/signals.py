"""
Activity-log signals for the content app. Using signals (rather than logging
inline in the viewsets) means an edit made through Django's built-in /admin/
site gets logged exactly like one made through the public API — one source
of truth for "what changed and when", matching lib/store.js's addLog() calls
in the original frontend prototype.
"""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from core.models import add_log
from .models import AboutBookingOption, AboutOccasion, Artist, GalleryItem, NewsPost, Service


@receiver(post_save, sender=NewsPost)
def log_news_saved(sender, instance, created, **kwargs):
    add_log('news', f'{"Added" if created else "Edited"} news post "{instance.title}"')


@receiver(post_delete, sender=NewsPost)
def log_news_deleted(sender, instance, **kwargs):
    add_log('news', f'Deleted news post "{instance.title}"')


@receiver(post_save, sender=Artist)
def log_artist_saved(sender, instance, created, **kwargs):
    add_log('artists', f'{"Added" if created else "Edited"} artist "{instance.name}"')


@receiver(post_delete, sender=Artist)
def log_artist_deleted(sender, instance, **kwargs):
    add_log('artists', f'Deleted artist "{instance.name}"')


@receiver(post_save, sender=GalleryItem)
def log_gallery_saved(sender, instance, created, **kwargs):
    add_log('gallery', f'{"Added" if created else "Edited"} gallery piece "{instance.title}"')


@receiver(post_delete, sender=GalleryItem)
def log_gallery_deleted(sender, instance, **kwargs):
    add_log('gallery', f'Deleted gallery piece "{instance.title}"')


@receiver(post_save, sender=Service)
def log_service_saved(sender, instance, created, **kwargs):
    add_log('services', f'{"Added" if created else "Edited"} service "{instance.name}"')


@receiver(post_delete, sender=Service)
def log_service_deleted(sender, instance, **kwargs):
    add_log('services', f'Deleted service "{instance.name}"')


@receiver(post_save, sender=AboutOccasion)
@receiver(post_delete, sender=AboutOccasion)
def log_about_occasion_changed(sender, instance, **kwargs):
    add_log('about', 'Updated About page occasions')


@receiver(post_save, sender=AboutBookingOption)
def log_about_option_saved(sender, instance, created, **kwargs):
    add_log('about', f'{"Added" if created else "Edited"} booking option "{instance.name}"')


@receiver(post_delete, sender=AboutBookingOption)
def log_about_option_deleted(sender, instance, **kwargs):
    add_log('about', f'Deleted booking option "{instance.name}"')
