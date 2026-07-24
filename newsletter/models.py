import uuid

from django.db import models


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=160, blank=True)
    is_active = models.BooleanField(default=True)
    # Identifies this subscriber on one-click unsubscribe links in campaign
    # emails without exposing the numeric id or requiring the visitor to log in.
    unsubscribe_token = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-subscribed_at']

    def __str__(self):
        return self.email
