from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from catalog.models import Wine


class Review(models.Model):
    """Wine reviews and ratings"""
    # Relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    wine = models.ForeignKey(Wine, on_delete=models.CASCADE, related_name='reviews')

    # Review content
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    title = models.CharField(max_length=200)
    comment = models.TextField()

    # Moderation
    is_approved = models.BooleanField(default=False, help_text="Approved by admin")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        unique_together = ['user', 'wine']  # One review per user per wine

    def __str__(self):
        return f"Review by {self.user.username} for {self.wine.name} ({self.rating}★)"
