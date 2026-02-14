from django.contrib import admin
from .models import Order, OrderItem, Cart, CartItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['price', 'get_total_price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total', 'created_at']
    search_fields = ['order_number', 'user__username', 'user__email', 'shipping_address']
    list_filter = ['status', 'created_at']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'subtotal', 'tax', 'total']
    list_editable = ['status']
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'wine', 'quantity', 'price', 'get_total_price']
    search_fields = ['order__order_number', 'wine__name']
    list_filter = ['created_at']


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_total_items', 'created_at', 'updated_at']
    search_fields = ['user__username']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'wine', 'quantity', 'added_at']
    search_fields = ['cart__user__username', 'wine__name']
    list_filter = ['added_at']
