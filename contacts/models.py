from django.db import models


class ContactSubmission(models.Model):
    name = models.CharField(max_length=160)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Set together, only via ContactSubmissionViewSet.reply — the message
    # itself stays immutable (see the ViewSet's docstring), this just tracks
    # whether/how staff responded.
    replied_at = models.DateTimeField(null=True, blank=True)
    reply_text = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} <{self.email}>'
