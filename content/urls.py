from rest_framework.routers import DefaultRouter

from .views import (
    AboutBookingOptionViewSet, AboutOccasionViewSet, AboutSummaryView, ArtistViewSet,
    FAQViewSet, GalleryItemViewSet, NewsPostViewSet, ServiceViewSet,
)
from django.urls import path

router = DefaultRouter()
router.register('news', NewsPostViewSet, basename='news')
router.register('artists', ArtistViewSet, basename='artist')
router.register('gallery', GalleryItemViewSet, basename='gallery')
router.register('services', ServiceViewSet, basename='service')
router.register('about/occasions', AboutOccasionViewSet, basename='about-occasion')
router.register('about/booking-options', AboutBookingOptionViewSet, basename='about-booking-option')
router.register('faq', FAQViewSet, basename='faq')

urlpatterns = [
    path('about/', AboutSummaryView.as_view(), name='about-summary'),
] + router.urls
