from django.conf import settings
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import (
    Ad,
    AdImage,
    Category,
    CustomerProfile,
    TemporaryAd,
    TemporaryAdImage,
)


def safe_increment_version(key_name):
    """
    Safely increments a cache version key.
    If the key does not exist in Redis, it safely initializes it to 1.
    """
    try:
        cache.incr(key_name)
    except ValueError:
        cache.set(key_name, 1)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_customer_for_user(sender, instance, **kwargs):
    """Save the Customer profile when User is saved."""
    try:
        instance.profile.save()
    except CustomerProfile.DoesNotExist:
        CustomerProfile.objects.create(user=instance)


@receiver([post_save, post_delete], sender=Category)
def invalidate_categories_cache(sender, instance, **kwargs):
    """Increments the categories cache version."""
    safe_increment_version("categories_cache_version")


@receiver([post_save, post_delete], sender=Ad)
def invalidate_ads_cache(sender, instance, **kwargs):
    """Increments all public and management ad cache versions independently."""
    safe_increment_version("ads_cache_version")
    safe_increment_version(f"ads_{instance.id}_cache_version")
    safe_increment_version(f"ads_manage_{instance.id}_cache_version")

    # Safely check if a customer relationship exists before accessing its ID
    if getattr(instance, "customer", None):
        safe_increment_version(
            f"ads_manage_customer_{instance.customer.id}_cache_version"
        )


@receiver([post_save, post_delete], sender=AdImage)
def invalidate_ads_images_cache(sender, instance, **kwargs):
    """Increments gallery and individual asset cache versions."""
    if getattr(instance, "ad", None):
        safe_increment_version(f"ads_images_{instance.ad.id}_cache_version")
    safe_increment_version(f"ads_image_{instance.id}_cache_version")


@receiver([post_save, post_delete], sender=TemporaryAd)
def invalidate_temp_ads_cache(sender, instance, **kwargs):
    """Increments temporary ad detail cache versions."""
    safe_increment_version(f"temp_ad_{instance.id}_cache_version")


@receiver([post_save, post_delete], sender=TemporaryAdImage)
def invalidate_temp_ads_images_cache(sender, instance, **kwargs):
    """Increments temporary gallery and individual asset cache versions."""
    if getattr(instance, "temporary_ad", None):
        safe_increment_version(
            f"temp_ads_images_{instance.temporary_ad.id}_cache_version"
        )
    safe_increment_version(f"temp_ads_image_{instance.id}_cache_version")
