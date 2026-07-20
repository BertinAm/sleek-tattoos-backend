from django.urls import path

from .views import (
    ConversationDetailView, ConversationListView, ConversationMarkReadView,
    ConversationMessagesView, ConversationResetView, ConversationStartView,
)

urlpatterns = [
    path('support/conversations/', ConversationStartView.as_view(), name='support-start'),
    path('support/conversations/list/', ConversationListView.as_view(), name='support-list'),
    path('support/conversations/<int:pk>/', ConversationDetailView.as_view(), name='support-detail'),
    path('support/conversations/<int:pk>/messages/', ConversationMessagesView.as_view(), name='support-messages'),
    path('support/conversations/<int:pk>/reset/', ConversationResetView.as_view(), name='support-reset'),
    path('support/conversations/<int:pk>/read/', ConversationMarkReadView.as_view(), name='support-read'),
]
