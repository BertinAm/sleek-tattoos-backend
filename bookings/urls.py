from rest_framework.routers import DefaultRouter

from .views import BookingViewSet, LocationViewSet

router = DefaultRouter()
router.register('bookings', BookingViewSet, basename='booking')
router.register('locations', LocationViewSet, basename='location')

urlpatterns = router.urls
