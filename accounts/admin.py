from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'city', 'country', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone_number', 'city']
    list_filter = ['country', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
