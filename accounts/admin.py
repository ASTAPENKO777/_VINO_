from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'city', 'country']
    search_fields = ['user__username', 'user__email', 'phone_number', 'city']
    list_filter = ['country']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Користувач', {
            'fields': ('user',)
        }),
        ('Контактна інформація', {
            'fields': ('phone_number', 'address', 'city', 'country', 'postal_code')
        }),
        ('Системні поля', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
