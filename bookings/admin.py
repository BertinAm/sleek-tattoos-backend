from django.contrib import admin

from .models import Booking, Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'travel_fee', 'order']
    ordering = ['order']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['name', 'appointment_type', 'location', 'preferred_date', 'preferred_time', 'status', 'created_at']
    list_filter = ['status', 'appointment_type']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['google_calendar_event_id', 'calendar_sync_error', 'created_at', 'updated_at']
