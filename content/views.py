from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsStaffOrReadOnly
from .models import AboutBookingOption, AboutOccasion, Artist, FAQ, GalleryItem, NewsPost, Service
from .serializers import (
    AboutBookingOptionSerializer, AboutOccasionSerializer, ArtistSerializer, FAQSerializer,
    GalleryItemSerializer, NewsPostSerializer, ServiceSerializer,
)


class NewsPostViewSet(viewsets.ModelViewSet):
    queryset = NewsPost.objects.all()
    serializer_class = NewsPostSerializer
    permission_classes = [IsStaffOrReadOnly]
    lookup_field = 'slug'


class ArtistViewSet(viewsets.ModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    permission_classes = [IsStaffOrReadOnly]
    lookup_field = 'slug'


class GalleryItemViewSet(viewsets.ModelViewSet):
    queryset = GalleryItem.objects.select_related('artist').all()
    serializer_class = GalleryItemSerializer
    permission_classes = [IsStaffOrReadOnly]


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsStaffOrReadOnly]


class AboutOccasionViewSet(viewsets.ModelViewSet):
    queryset = AboutOccasion.objects.all()
    serializer_class = AboutOccasionSerializer
    permission_classes = [IsStaffOrReadOnly]


class AboutBookingOptionViewSet(viewsets.ModelViewSet):
    queryset = AboutBookingOption.objects.all()
    serializer_class = AboutBookingOptionSerializer
    permission_classes = [IsStaffOrReadOnly]


class AboutSummaryView(APIView):
    """GET /api/about/ — combined {occasions, services} shape, matching the
    frontend's old getAbout() so the About page can fetch in one call."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'occasions': AboutOccasionSerializer(AboutOccasion.objects.all(), many=True).data,
            'services': AboutBookingOptionSerializer(AboutBookingOption.objects.all(), many=True).data,
        })


class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [IsStaffOrReadOnly]
