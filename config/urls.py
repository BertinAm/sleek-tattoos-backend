"""
Root URL configuration. Every API route lives under /api/ so the Django
admin (/admin/) and any future non-API routes never collide with it.

Full endpoint reference: see implementation.md.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.views import RobotsView

urlpatterns = [
    path('robots.txt', RobotsView.as_view(), name='robots'),
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/', include('content.urls')),
    path('api/', include('bookings.urls')),
    path('api/', include('contacts.urls')),
    path('api/', include('support.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
