from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'wine', 'rating', 'title', 'is_approved', 'created_at']
    search_fields = ['user__username', 'wine__name', 'title', 'comment']
    list_filter = ['rating', 'is_approved', 'created_at']
    list_editable = ['is_approved']
    readonly_fields = ['created_at', 'updated_at']
