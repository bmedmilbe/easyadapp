# ads/signals.py
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomerProfile

# @receiver(post_save, sender=settings.AUTH_USER_MODEL)
# def create_customer_for_user(sender, instance, created, **kwargs):
#     """Create a Customer profile when a new User is created."""
#     if created:
#         CustomerProfile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_customer_for_user(sender, instance, **kwargs):
    """Save the Customer profile when User is saved."""
    try:
        instance.profile.save()
    except CustomerProfile.DoesNotExist:
        # If customer doesn't exist (shouldn't happen), create it
        CustomerProfile.objects.create(user=instance)