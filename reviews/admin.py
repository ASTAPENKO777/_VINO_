from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['wine', 'user', 'rating_stars', 'title', 'is_approved', 'created_at']
    search_fields = ['user__username', 'wine__name', 'title']
    list_filter = ['is_approved', 'rating']
    list_editable = ['is_approved']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 25

    @admin.display(description='Оцінка')
    def rating_stars(self, obj):
        return '★' * obj.rating + '☆' * (5 - obj.rating)
