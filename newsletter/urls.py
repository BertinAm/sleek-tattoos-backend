from django.urls import path

from .views import SubscribeView, SubscriberDetailView, SubscriberListView, UnsubscribeView

urlpatterns = [
    path('newsletter/subscribe/', SubscribeView.as_view(), name='newsletter-subscribe'),
    path('newsletter/unsubscribe/<uuid:token>/', UnsubscribeView.as_view(), name='newsletter-unsubscribe'),
    path('newsletter/subscribers/', SubscriberListView.as_view(), name='newsletter-subscribers'),
    path('newsletter/subscribers/<int:pk>/', SubscriberDetailView.as_view(), name='newsletter-subscriber-detail'),
]
