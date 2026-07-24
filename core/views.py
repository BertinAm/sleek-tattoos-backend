import logging

from django.core.files.storage import default_storage
from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .emailing import send_admin_login_notification
from .models import ActivityLog, add_log
from .permissions import IsStaffOnly
from .serializers import ActivityLogSerializer, ImageUploadSerializer, UserSerializer

logger = logging.getLogger(__name__)


class LoginView(TokenObtainPairView):
    """POST {username, password} -> {access, refresh}. Logs the event like
    the old mock login() did, but with real credential checking this time.

    Throttled to 5/min per IP ('login' scope, see settings.py) — the admin
    panel is the only thing that calls this, so a real user retrying a typo
    a few times never notices, but credential-stuffing/brute-force gets
    capped hard. Deliberately per-IP (not per-username) since this endpoint
    is unauthenticated by definition."""
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            username = request.data.get('username', '')
            add_log('auth', f'Admin logged in ({username})')
            try:
                error = send_admin_login_notification(username, request.META.get('REMOTE_ADDR'))
                if error:
                    logger.warning('Admin login notification email failed: %s', error)
            except Exception:  # emailing.py already catches internally; this is a last-resort net
                logger.exception('Admin login notification email failed unexpectedly')
        return response


class LogoutView(APIView):
    """POST {refresh} -> blacklists the refresh token so it can't be reused.
    Access tokens remain valid until they naturally expire (short-lived by design)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get('refresh')
        if not refresh:
            return Response({'detail': 'refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(refresh).blacklist()
        except Exception:
            # Already invalid/expired — logout still "succeeds" from the client's POV.
            pass
        add_log('auth', f'Admin logged out ({request.user.username})')
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ActivityLogListView(generics.ListAPIView):
    """GET /api/logs/ — admin-only, newest first, matches the Activity Logs page."""
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    permission_classes = [IsStaffOnly]


class ImageUploadView(APIView):
    """POST multipart {file} -> {url}. Public, not staff-only — the booking
    form uses this too (customers attaching reference tattoo images before
    they're anyone's "admin"). Admin content forms (News/Gallery/Artist/
    Service) also call this first, then send the returned URL back as the
    `image` field. Rate-limited (`public_write` scope, 20/min/IP) — see
    settings.py; ImageUploadSerializer separately caps file size and verifies
    the upload is a genuine image, not just an image-looking filename."""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'public_write'

    def post(self, request):
        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        f = serializer.validated_data['file']
        path = default_storage.save(f'uploads/{f.name}', f)
        url = request.build_absolute_uri(default_storage.url(path))
        return Response({'url': url}, status=status.HTTP_201_CREATED)


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'ok'})


class RobotsView(APIView):
    """GET /robots.txt — this whole origin is an API, never a page a search
    engine should index. Mounted at the domain root in config/urls.py, not
    under /api/, since crawlers only ever check /robots.txt."""
    permission_classes = [AllowAny]

    def get(self, request):
        return HttpResponse('User-agent: *\nDisallow: /\n', content_type='text/plain')
