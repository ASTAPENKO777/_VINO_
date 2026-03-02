from django.contrib import admin
from .models import Order, OrderItem, Cart, CartItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['item_total']
    can_delete = False

    @admin.display(description='Сума')
    def item_total(self, obj):
        if obj.pk and obj.quantity is not None and obj.price is not None:
            return f'{obj.get_total_price()} ₴'
        return '—'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'recipient', 'status', 'total_display', 'created_at']
    search_fields = ['order_number', 'user__username', 'last_name', 'first_name', 'phone_number']
    list_filter = ['status']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'subtotal', 'tax', 'total']
    list_editable = ['status']
    list_per_page = 25
    inlines = [OrderItemInline]

    fieldsets = (
        ('Замовлення', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('Отримувач', {
            'fields': ('last_name', 'first_name', 'patronymic', 'phone_number')
        }),
        ('Доставка', {
            'fields': ('shipping_address', 'shipping_city', 'shipping_country', 'shipping_postal_code')
        }),
        ('Сума', {
            'fields': ('subtotal', 'tax', 'shipping_cost', 'total'),
            'classes': ('collapse',),
        }),
        ('Примітки', {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),
        ('Системні поля', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Отримувач')
    def recipient(self, obj):
        return obj.recipient_full_name or obj.user.username

    @admin.display(description='Сума')
    def total_display(self, obj):
        return f'{obj.total} ₴'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'items_count', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']

    @admin.display(description='Товарів')
    def items_count(self, obj):
        return obj.get_total_items()


