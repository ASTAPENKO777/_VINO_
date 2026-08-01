from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from catalog.models import Wine
from decimal import Decimal

from . import pricing


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Очікує'),
        ('confirmed', 'Підтверджено'),
        ('processing', 'Обробляється'),
        ('shipped', 'Відправлено'),
        ('delivered', 'Доставлено'),
        ('cancelled', 'Скасовано'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_country = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)

    phone_number = models.CharField(max_length=20)

    last_name = models.CharField(max_length=100, verbose_name='Прізвище', default='')
    first_name = models.CharField(max_length=100, verbose_name='Ім\'я', default='')
    patronymic = models.CharField(max_length=100, blank=True, default='', verbose_name='По батькові')

    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'
        ordering = ['-created_at']

    @property
    def recipient_full_name(self):
        parts = [self.last_name, self.first_name]
        if self.patronymic:
            parts.append(self.patronymic)
        return ' '.join(parts)

    def __str__(self):
        return f"Order {self.order_number} by {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = f"ORD-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def calculate_totals(self):
        subtotal = sum(
            (item.get_total_price() for item in self.items.all()),
            Decimal('0'),
        )
        self.subtotal = pricing.money(subtotal)
        self.tax = pricing.tax_for(self.subtotal)
        self.shipping_cost = pricing.shipping_for(self.subtotal)
        self.total = pricing.money(self.subtotal + self.tax + self.shipping_cost)
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    wine = models.ForeignKey(Wine, on_delete=models.PROTECT, related_name='order_items')

    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)  

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Позиція замовлення'
        verbose_name_plural = 'Позиції замовлення'
        unique_together = ['order', 'wine']

    def __str__(self):
        return f"{self.quantity}x {self.wine.name} in {self.order.order_number}"

    def get_total_price(self):
        return self.quantity * self.price


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Кошик'
        verbose_name_plural = 'Кошики'

    def __str__(self):
        return f"Cart of {self.user.username}"

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())

    def clear(self):
        self.items.all().delete()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    wine = models.ForeignKey(Wine, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.IntegerField(validators=[MinValueValidator(1)], default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Позиція кошика'
        verbose_name_plural = 'Позиції кошика'
        unique_together = ['cart', 'wine']

    def __str__(self):
        return f"{self.quantity}x {self.wine.name} in cart"

    def get_total_price(self):
        return self.quantity * self.wine.price