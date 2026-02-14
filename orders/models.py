from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from catalog.models import Wine
from decimal import Decimal


class Order(models.Model):
    """Customer orders"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    # Relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')

    # Order details
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Shipping information
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_country = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)

    # Contact
    phone_number = models.CharField(max_length=20)

    # Notes
    notes = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number} by {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = f"ORD-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Recalculate order totals from items"""
        self.subtotal = sum(item.get_total_price() for item in self.items.all())
        self.tax = self.subtotal * Decimal('0.10')  # 10% tax
        self.total = self.subtotal + self.tax + self.shipping_cost
        self.save()


class OrderItem(models.Model):
    """Individual items in an order"""
    # Relationships
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    wine = models.ForeignKey(Wine, on_delete=models.PROTECT, related_name='order_items')

    # Item details
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        unique_together = ['order', 'wine']

    def __str__(self):
        return f"{self.quantity}x {self.wine.name} in {self.order.order_number}"

    def get_total_price(self):
        return self.quantity * self.price


class Cart(models.Model):
    """Shopping cart for logged-in users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'

    def __str__(self):
        return f"Cart of {self.user.username}"

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())

    def clear(self):
        """Remove all items from cart"""
        self.items.all().delete()


class CartItem(models.Model):
    """Items in shopping cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    wine = models.ForeignKey(Wine, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.IntegerField(validators=[MinValueValidator(1)], default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        unique_together = ['cart', 'wine']

    def __str__(self):
        return f"{self.quantity}x {self.wine.name} in cart"

    def get_total_price(self):
        return self.quantity * self.wine.price
