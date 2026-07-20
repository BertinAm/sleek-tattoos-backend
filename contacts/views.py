from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle

from core.permissions import IsStaffOnly
from .models import ContactSubmission
from .serializers import ContactSubmissionSerializer


class ContactSubmissionViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                                mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """POST is public (the contact form). List/retrieve/delete are admin-only —
    there's no legitimate reason to update a submitted message, so no PUT/PATCH."""
    queryset = ContactSubmission.objects.all()
    serializer_class = ContactSubmissionSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsStaffOnly()]

    def get_throttles(self):
        if self.action == 'create':
            self.throttle_scope = 'public_write'
            return [ScopedRateThrottle()]
        return super().get_throttles()
