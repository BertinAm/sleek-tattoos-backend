from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['type', 'message', 'created_at']
    list_filter = ['type']
    ordering = ['-created_at']
