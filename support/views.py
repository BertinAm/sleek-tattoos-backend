from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from core.models import add_log
from core.permissions import IsStaffOnly
from .bot import GREETING, match_answer
from .models import Conversation, Message
from .serializers import ConversationListSerializer, ConversationSerializer, SendMessageSerializer


def _owns_conversation(request, conversation) -> bool:
    """A visitor "owns" a conversation if their token (sent as a header, since
    it's easier for the frontend to attach consistently than juggling query
    params on every verb) matches — or if they're staff."""
    if request.user and request.user.is_authenticated and request.user.is_staff:
        return True
    token = request.headers.get('X-Visitor-Token') or request.query_params.get('visitor_token')
    return str(conversation.visitor_token) == token


class ConversationListView(generics.ListAPIView):
    """GET /api/support/conversations/ — admin inbox, newest activity first."""
    serializer_class = ConversationListSerializer
    permission_classes = [IsStaffOnly]
    queryset = Conversation.objects.all().prefetch_related('messages')

    def get_queryset(self):
        return sorted(self.queryset.all(), key=lambda c: c.last_message_at, reverse=True)


class ConversationStartView(APIView):
    """POST /api/support/conversations/ {visitor_token?} -> conversation.
    No token, or an unknown one, creates a brand new conversation (seeded
    with the greeting message) and returns its fresh visitor_token — the
    frontend is expected to persist that and send it back on every future call."""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'public_write'

    def post(self, request):
        token = request.data.get('visitor_token')
        conversation = None
        if token:
            conversation = Conversation.objects.filter(visitor_token=token).first()
        if conversation is None:
            count = Conversation.objects.count() + 1
            conversation = Conversation.objects.create(name=f'Website Visitor #{count}')
            Message.objects.create(conversation=conversation, sender='bot', text=GREETING)
        return Response(ConversationSerializer(conversation).data, status=status.HTTP_200_OK)


class ConversationDetailView(APIView):
    """GET /api/support/conversations/{id}/ — visitor (matching token) or staff."""
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if not _owns_conversation(request, conversation):
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(ConversationSerializer(conversation).data)


class ConversationMessagesView(APIView):
    """POST /api/support/conversations/{id}/messages/ {text}
    - Visitor (matching token): posts as 'user', triggers an instant bot reply, marks unread.
    - Staff: posts as 'admin', marks read.

    Throttled at the 'public_write' scope — keyed per-user for authenticated
    staff and per-IP for anonymous visitors (DRF's default), so a burst of
    visitor chat messages from one IP never affects a logged-in admin's
    ability to reply.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'public_write'

    def post(self, request, pk):
        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        is_staff = bool(request.user and request.user.is_authenticated and request.user.is_staff)
        if not is_staff and not _owns_conversation(request, conversation):
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        text = serializer.validated_data['text']

        if is_staff:
            Message.objects.create(conversation=conversation, sender='admin', text=text)
            conversation.unread = False
            conversation.save(update_fields=['unread'])
            add_log('support', f'Admin replied to {conversation.name}')
        else:
            Message.objects.create(conversation=conversation, sender='user', text=text)
            conversation.unread = True
            conversation.save(update_fields=['unread'])
            add_log('support', f'New support message from {conversation.name}: "{text[:60]}"')
            answer = match_answer(text)
            Message.objects.create(conversation=conversation, sender='bot', text=answer)

        return Response(ConversationSerializer(conversation).data, status=status.HTTP_201_CREATED)


class ConversationResetView(APIView):
    """POST /api/support/conversations/{id}/reset/ — visitor or staff, wipes
    history back to a single fresh greeting (matches the widget's "new chat" button)."""
    permission_classes = [AllowAny]

    def post(self, request, pk):
        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if not _owns_conversation(request, conversation):
            return Response(status=status.HTTP_403_FORBIDDEN)
        conversation.messages.all().delete()
        Message.objects.create(conversation=conversation, sender='bot', text=GREETING)
        conversation.unread = False
        conversation.save(update_fields=['unread'])
        return Response(ConversationSerializer(conversation).data)


class ConversationMarkReadView(APIView):
    """POST /api/support/conversations/{id}/read/ — admin-only, click-to-open in the inbox."""
    permission_classes = [IsStaffOnly]

    def post(self, request, pk):
        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        conversation.unread = False
        conversation.save(update_fields=['unread'])
        return Response(ConversationSerializer(conversation).data)
