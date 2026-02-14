from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.urls import reverse


class WineType(models.Model):
    """Wine type classification (Red, White, Rose, Sparkling, etc.)"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Wine Type'
        verbose_name_plural = 'Wine Types'
        ordering = ['name']

    def __str__(self):
        return self.name


class Country(models.Model):
    """Wine origin countries"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=3, unique=True, help_text="ISO country code")

    class Meta:
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'
        ordering = ['name']

    def __str__(self):
        return self.name


class Wine(models.Model):
    """Main wine product model"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    photo = models.ImageField(upload_to='wines/%Y/%m/%d/', blank=True, null=True)

    # Relationships
    wine_type = models.ForeignKey(WineType, on_delete=models.PROTECT, related_name='wines')
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='wines')

    # Wine characteristics
    year = models.IntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2026)],
        help_text="Vintage year"
    )
    alcohol_content = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    volume_ml = models.IntegerField(default=750, help_text="Bottle volume in ml")

    # Inventory
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True, help_text="Available for purchase")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Wine'
        verbose_name_plural = 'Wines'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['wine_type', 'country']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return f"{self.name} ({self.year})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.year}")
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalog:wine_detail', kwargs={'slug': self.slug})

    @property
    def in_stock(self):
        return self.stock_quantity > 0

    @property
    def average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return reviews.aggregate(models.Avg('rating'))['rating__avg']
        return None
