from django.contrib import admin
from django.utils.html import format_html
from .models import WineType, Country, Wine


@admin.register(WineType)
class WineTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name']


@admin.register(Wine)
class WineAdmin(admin.ModelAdmin):
    list_display = ['name', 'wine_type', 'country', 'year', 'price_display', 'stock_quantity', 'is_active']
    search_fields = ['name', 'wine_type__name', 'country__name']
    list_filter = ['wine_type', 'country', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['price', 'stock_quantity', 'is_active']
    list_per_page = 25

    fieldsets = (
        ('Основна інформація', {
            'fields': ('name', 'slug', 'wine_type', 'country', 'year', 'description', 'photo')
        }),
        ('Ціна та наявність', {
            'fields': ('price', 'stock_quantity', 'is_active')
        }),
        ('Характеристики', {
            'fields': ('alcohol_content', 'volume_ml'),
            'classes': ('collapse',),
        }),
        ('Системні поля', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Ціна, ₴')
    def price_display(self, obj):
        return f'{obj.price} ₴'

    list_display = ['name', 'wine_type', 'country', 'year', 'price', 'stock_quantity', 'is_active']
