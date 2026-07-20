import uuid

from django.db import models


class Conversation(models.Model):
    """One per site visitor. `visitor_token` is a random ID the frontend
    stores (localStorage, matching the old prototype's sk_support_visitor_id)
    and sends back on every request — there's no real visitor auth, this is
    a low-stakes support widget, not an account system."""
    visitor_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=160, default='Website Visitor')
    unread = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.name

    @property
    def last_message_at(self):
        last = self.messages.last()
        return last.created_at if last else self.created_at


class Message(models.Model):
    FROM_CHOICES = [('user', 'user'), ('bot', 'bot'), ('admin', 'admin'), ('system', 'system')]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=FROM_CHOICES)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender}: {self.text[:40]}'
