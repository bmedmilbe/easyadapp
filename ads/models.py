# ads/models.py
import os
import uuid
from datetime import timedelta
from io import BytesIO

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from PIL import Image


class CustomerProfile(models.Model):
    """
    Customer profile model that links to the user model via OneToOneField.
    This is the ONLY model that directly links to the user model.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer Profile"
        verbose_name_plural = "Customer Profiles"

    def __str__(self):
        return f"Profile for {self.user.mobile_number}"

    @property
    def whatsapp_link(self):
        """
        Returns a sanitized WhatsApp link for the user's mobile number.
        """
        if not self.user.mobile_number:
            return "#"

        # Remove any non-numeric characters from the mobile number
        clean_number = "".join(filter(str.isdigit, self.user.mobile_number))

        # Remove any leading zeros or country code indicators
        clean_number = clean_number.removeprefix("0")

        return f"https://wa.me/{clean_number}"


# ads/models.py - Update Category model
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=10, blank=True, help_text="Emoji or icon for the category"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return f"{self.icon or '📁'} {self.name}"


class AdStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    SUSPENDED = "SUSPENDED", "Suspended"
    EXPIRED = "EXPIRED", "Expired"


class AdCondition(models.TextChoices):
    NEW = "NEW", "Novo"
    USED = "USED", "Usado"
    IMPORTED = "IMPORTED", "Importado"
    LOCAL = "LOCAL", "Produzido em São Tomé"


def default_expiration_date():
    """
    Returns a datetime 7 days from now.
    """
    return timezone.now() + timedelta(days=7)


class Ad(models.Model):
    """
    Main ad model that links to CustomerProfile (not directly to User).
    All ads are free and active by default.
    """

    customer = models.ForeignKey(
        CustomerProfile, on_delete=models.CASCADE, related_name="ads"
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="ads"
    )
    condition = models.CharField(
        max_length=20,
        choices=AdCondition.choices,
        default=AdCondition.NEW,
        verbose_name="Condição do Produto",
    )
    product_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Status and expiration
    status = models.CharField(
        max_length=20, choices=AdStatus.choices, default=AdStatus.ACTIVE
    )
    expires_at = models.DateTimeField(default=default_expiration_date)

    # Premium flag for featured listings
    is_featured = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ad"
        verbose_name_plural = "Ads"
        ordering = ["-is_featured", "-created_at"]  # Featured ads float to top

    def __str__(self):
        return f"{self.product_name} - {self.customer.user.mobile_number}"

    def is_expired(self):
        """
        Check if the ad has expired.
        """
        return timezone.now() >= self.expires_at

    def save(self, *args, **kwargs):
        """
        Override save to automatically set status to EXPIRED if expired.
        """
        if self.is_expired():
            self.status = AdStatus.EXPIRED
        super().save(*args, **kwargs)


class AdImage(models.Model):
    """
    Model for storing multiple images per ad.
    """

    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="ads/ad_images/")
    api_image_webp = models.ImageField(upload_to="ads/ad_images_webp/", blank=True, null=True)
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Ad Image"
        verbose_name_plural = "Ad Images"
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Image for {self.ad.product_name}"

    
class TemporaryAd(models.Model):
    """
    Temporary draft holding station for non-authenticated users.
    No relationship to User or CustomerProfile.
    """

    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True)

    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="temporary_ads"
    )
    product_name = models.CharField(max_length=200, null=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Temporary Ad"
        verbose_name_plural = "Temporary Ads"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Temporary: {self.product_name} ({self.session_token})"

    def transfer_to_official_ad(self, customer_profile):
        """
        Transfer the temporary ad to an official production Ad record.

        Args:
            customer_profile: The CustomerProfile instance to associate the new ad with.

        Returns:
            Ad: The newly created official ad.
        """
        if not customer_profile or not isinstance(customer_profile, CustomerProfile):
            raise ValidationError("A valid CustomerProfile is required.")

        # Create the official ad
        official_ad = Ad.objects.create(
            customer=customer_profile,
            category=self.category,
            product_name=self.product_name,
            description=self.description,
            price=self.price,
            status=AdStatus.ACTIVE,  # Active by default
            is_featured=False,  # Not featured by default
        )

        # Migrate all related temporary images to the official ad
        temp_images = self.temporary_images.all()
        for temp_image in temp_images:
            AdImage.objects.create(
                ad=official_ad,
                image=temp_image.image,
                api_image_webp=temp_image.api_image_webp,
                caption=temp_image.caption,
                order=temp_image.order,
            )

        # Delete the temporary ad and its images
        self.delete()

        return official_ad


class TemporaryAdImage(models.Model):
    """
    Model for storing multiple images per temporary ad.
    """

    temporary_ad = models.ForeignKey(
        TemporaryAd, on_delete=models.CASCADE, related_name="temporary_images"
    )
    image = models.ImageField(upload_to="ads/temp_ad_images/")
    api_image_webp = models.ImageField(upload_to="ads/temp_ad_images_webp/", blank=True, null=True)

    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Temporary Ad Image"
        verbose_name_plural = "Temporary Ad Images"
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Temp Image for {self.temporary_ad.product_name}"

    def save(self, *args, **kwargs):
        # Process only if an image exists and the optimized WebP hasn't been created yet
        if self.image and not self.api_image_webp:

            # 1. Environment-Agnostic File Open
            self.image.open()
            self.image.seek(0)

            # Read into memory so Pillow doesn't lock the active file connection
            image_bytes = BytesIO(self.image.read())
            img = Image.open(image_bytes)

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
    
            # 2. Dimensions & Padding
            target_size = (1200, 1200)
            canvas = Image.new("RGB", target_size, (255, 255, 255))

            # Downscale safely without altering small images
            img.thumbnail(target_size, Image.Resampling.LANCZOS)

            # Center on canvas
            offset = ((target_size[0] - img.size[0]) // 2, (target_size[1] - img.size[1]) // 2)
            canvas.paste(img, offset)
    
            # 3. Save optimized canvas to memory
            buffer = BytesIO()
            canvas.save(buffer, format="WEBP", quality=85, optimize=True)
            buffer.seek(0)
    
            # 4. Clean Filename Extraction
            raw_filename = os.path.basename(self.image.name)
            name_without_ext, _ = os.path.splitext(raw_filename)

            # 5. Assign to the field without triggering an early save network call
            self.api_image_webp.save(
                f"{name_without_ext}_api.webp", 
                ContentFile(buffer.read()), 
                save=False
            )

            # REMOVED self.image.close() completely to avoid I/O errors!
    
        # 6. Fallback to standard Django saving behavior
        super().save(*args, **kwargs)
