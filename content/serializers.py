from rest_framework import serializers

from .models import AboutBookingOption, AboutOccasion, Artist, FAQ, GalleryItem, NewsPost, Service


class ArtistSerializer(serializers.ModelSerializer):
    gallery_count = serializers.IntegerField(source='gallery_items.count', read_only=True)

    class Meta:
        model = Artist
        fields = ['id', 'slug', 'name', 'role', 'specialty', 'bio', 'portrait', 'gallery_count']


class NewsPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsPost
        fields = ['id', 'slug', 'category', 'title', 'date', 'image', 'excerpt', 'body', 'author', 'tags']


class GalleryItemSerializer(serializers.ModelSerializer):
    artist_slug = serializers.SlugRelatedField(
        source='artist', slug_field='slug', queryset=Artist.objects.all(), required=False, allow_null=True,
    )
    artist_name = serializers.CharField(source='artist.name', read_only=True, default='')

    class Meta:
        model = GalleryItem
        fields = ['id', 'category', 'title', 'image', 'artist_slug', 'artist_name']


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'price_label', 'description', 'examples', 'cart_value', 'image', 'order']


class AboutOccasionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutOccasion
        fields = ['id', 'label', 'order']


class AboutBookingOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutBookingOption
        fields = ['id', 'icon', 'name', 'description', 'order']


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'order']
