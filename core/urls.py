from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import ActivityLogListView, HealthCheckView, ImageUploadView, LoginView, LogoutView, MeView

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
    path('logs/', ActivityLogListView.as_view(), name='logs-list'),
    path('uploads/images/', ImageUploadView.as_view(), name='upload-image'),
    path('health/', HealthCheckView.as_view(), name='health'),
]
