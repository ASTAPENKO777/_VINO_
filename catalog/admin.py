from django.contrib import admin
from .models import WineType, Country, Wine


@admin.register(WineType)
class WineTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']
    list_filter = ['code']


@admin.register(Wine)
class WineAdmin(admin.ModelAdmin):
    list_display = ['name', 'wine_type', 'country', 'year', 'price', 'stock_quantity', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'wine_type__name', 'country__name']
    list_filter = ['wine_type', 'country', 'year', 'is_active', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['price', 'stock_quantity', 'is_active']
