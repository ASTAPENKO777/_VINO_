from django.db.models.signals import post_save, post_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Order, OrderItem, Cart
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_cart(sender, instance, created, **kwargs):
    if created:
        Cart.objects.create(user=instance)
        logger.info(f"Cart created for user: {instance.username}")


@receiver(post_save, sender=Order)
def log_order_status_change(sender, instance, created, **kwargs):
    if created:
        logger.info(f"New order created: {instance.order_number} by {instance.user.username}")
    else:
        logger.info(f"Order {instance.order_number} status changed to: {instance.status}")


@receiver(post_save, sender=OrderItem)
def update_stock_on_order_item_create(sender, instance, created, **kwargs):
    if created:
        wine = instance.wine
        wine.stock_quantity -= instance.quantity
        wine.save()
        logger.warning(f"Stock reduced for {wine.name}: -{instance.quantity} (remaining: {wine.stock_quantity})")


@receiver(post_delete, sender=OrderItem)
def restore_stock_on_order_item_delete(sender, instance, **kwargs):
    wine = instance.wine
    wine.stock_quantity += instance.quantity
    wine.save()
    logger.info(f"Stock restored for {wine.name}: +{instance.quantity}")
