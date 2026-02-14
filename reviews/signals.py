from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Review
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Review)
def log_review_action(sender, instance, created, **kwargs):
    """Log review creation and approval"""
    if created:
        logger.info(f"New review created by {instance.user.username} for {instance.wine.name}")
    elif instance.is_approved:
        logger.info(f"Review approved for {instance.wine.name} by {instance.user.username}")


@receiver(post_delete, sender=Review)
def log_review_deletion(sender, instance, **kwargs):
    """Log review deletion"""
    logger.warning(f"Review deleted by {instance.user.username} for {instance.wine.name}")
