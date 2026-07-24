import logging

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from core.emailing import send_contact_notification, send_contact_reply
from core.models import add_log
from core.permissions import IsStaffOnly
from django.utils import timezone
from .models import ContactSubmission
from .serializers import ContactReplySerializer, ContactSubmissionSerializer

logger = logging.getLogger(__name__)


class ContactSubmissionViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                                mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """POST is public (the contact form). List/retrieve/delete are admin-only —
    there's no legitimate reason to update the submitted *message*, so no
    general PUT/PATCH — the one exception is the `reply` action below, which
    only ever touches replied_at/reply_text, never name/email/phone/message."""
    queryset = ContactSubmission.objects.all()
    serializer_class = ContactSubmissionSerializer

    def get_permissions(self):
        if self.action in ('create', 'reply'):
            return [AllowAny()] if self.action == 'create' else [IsStaffOnly()]
        return [IsStaffOnly()]

    def get_throttles(self):
        if self.action == 'create':
            self.throttle_scope = 'public_write'
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def perform_create(self, serializer):
        contact = serializer.save()
        try:
            error = send_contact_notification(contact)
            if error:
                logger.warning('Contact notification email failed for submission %s: %s', contact.pk, error)
        except Exception:  # emailing.py already catches internally; this is a last-resort net
            logger.exception('Contact notification email failed unexpectedly for submission %s', contact.pk)

    @action(detail=True, methods=['post'], permission_classes=[IsStaffOnly])
    def reply(self, request, pk=None):
        """POST /api/contacts/{id}/reply/ {message} — emails the customer
        directly (from hello@) and records that + when on the submission."""
        contact = self.get_object()
        serializer = ContactReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reply_text = serializer.validated_data['message']

        error = send_contact_reply(contact, reply_text)
        if error:
            return Response({'detail': f'Failed to send reply email: {error}'}, status=status.HTTP_502_BAD_GATEWAY)

        contact.reply_text = reply_text
        contact.replied_at = timezone.now()
        contact.save(update_fields=['reply_text', 'replied_at'])
        add_log('contact', f'Replied to contact submission from {contact.name}')
        return Response(ContactSubmissionSerializer(contact).data)
