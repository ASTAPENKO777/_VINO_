from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from catalog.models import Wine


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    wine = models.ForeignKey(Wine, on_delete=models.CASCADE, related_name='reviews')

    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    title = models.CharField(max_length=200)
    comment = models.TextField()

    is_approved = models.BooleanField(default=False, help_text="Approved by admin")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Відгук'
        verbose_name_plural = 'Відгуки'
        ordering = ['-created_at']
        unique_together = ['user', 'wine']

    def __str__(self):
        return f"Review by {self.user.username} for {self.wine.name} ({self.rating}★)"
