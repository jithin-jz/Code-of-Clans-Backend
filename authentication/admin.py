from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'provider', 'provider_id', 'created_at']
    list_filter = ['provider', 'created_at']
    search_fields = ['user__username', 'user__email', 'provider_id']
    readonly_fields = ['created_at', 'updated_at']
