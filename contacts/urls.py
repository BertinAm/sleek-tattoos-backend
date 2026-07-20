from rest_framework.routers import DefaultRouter

from .views import ContactSubmissionViewSet

router = DefaultRouter()
router.register('contacts', ContactSubmissionViewSet, basename='contact')

urlpatterns = router.urls
