from django.contrib import admin

from .models import AboutBookingOption, AboutOccasion, Artist, FAQ, GalleryItem, NewsPost, Service


@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'date', 'author']
    list_filter = ['category']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'author']


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'specialty']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'artist']
    list_filter = ['category']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_label', 'cart_value', 'order']
    ordering = ['order']


@admin.register(AboutOccasion)
class AboutOccasionAdmin(admin.ModelAdmin):
    list_display = ['label', 'order']


@admin.register(AboutBookingOption)
class AboutBookingOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'order']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'order']
