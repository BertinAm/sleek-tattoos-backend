import logging

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from core.models import add_log
from core.permissions import IsStaffOnly
from .models import Subscriber
from .serializers import SubscribeSerializer, SubscriberSerializer

logger = logging.getLogger(__name__)


class SubscribeView(APIView):
    """POST /api/newsletter/subscribe/ {email, name?} — public. Reactivates
    an existing inactive subscriber instead of erroring on the unique
    constraint, so someone who unsubscribed can just sign up again."""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'public_write'

    def post(self, request):
        serializer = SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        name = serializer.validated_data['name']

        subscriber, created = Subscriber.objects.get_or_create(email=email, defaults={'name': name})
        if not created:
            update_fields = []
            if not subscriber.is_active:
                subscriber.is_active = True
                subscriber.unsubscribed_at = None
                update_fields += ['is_active', 'unsubscribed_at']
                add_log('newsletter', f'{subscriber.email} re-subscribed to the mailing list')
            if name and name != subscriber.name:
                subscriber.name = name
                update_fields.append('name')
            if update_fields:
                subscriber.save(update_fields=update_fields)

        return Response(SubscriberSerializer(subscriber).data, status=status.HTTP_201_CREATED)


class UnsubscribeView(APIView):
    """GET /api/newsletter/unsubscribe/{token}/ — public, one click from a
    campaign email's footer link. GET (not POST) so a plain <a href> works."""
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            subscriber = Subscriber.objects.get(unsubscribe_token=token)
        except (Subscriber.DoesNotExist, ValueError):
            return Response({'detail': 'Invalid or expired unsubscribe link.'}, status=status.HTTP_404_NOT_FOUND)

        if subscriber.is_active:
            subscriber.is_active = False
            subscriber.unsubscribed_at = timezone.now()
            subscriber.save(update_fields=['is_active', 'unsubscribed_at'])
            add_log('newsletter', f'{subscriber.email} unsubscribed from the mailing list')

        return Response({'email': subscriber.email, 'unsubscribed': True})


class SubscriberListView(generics.ListAPIView):
    """GET /api/newsletter/subscribers/ — admin list, newest first."""
    serializer_class = SubscriberSerializer
    permission_classes = [IsStaffOnly]
    queryset = Subscriber.objects.all()


class SubscriberDetailView(APIView):
    """DELETE /api/newsletter/subscribers/{id}/ — admin removes a subscriber outright."""
    permission_classes = [IsStaffOnly]

    def delete(self, request, pk):
        try:
            subscriber = Subscriber.objects.get(pk=pk)
        except Subscriber.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        email = subscriber.email
        subscriber.delete()
        add_log('newsletter', f'Removed {email} from the mailing list')
        return Response(status=status.HTTP_204_NO_CONTENT)
