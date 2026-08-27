from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from PIL import Image

from ads.models import (
    Ad,
    AdCondition,
    AdImage,
    AdStatus,
    Category,
    TemporaryAd,
    TemporaryAdImage,
    default_expiration_date,
)

User = get_user_model()


def create_new_valid_user():
    user = User.objects.create_user(
        mobile_number="+2399912345",
        username="testuser",
        district="AGUA_GRANDE",
        password="password123",
    )
    return user


class CustomerProfileModelTest(TestCase):
    def setUp(self):
        # Create user with a mobile number attribute matching model design
        self.user = create_new_valid_user()
        self.user.save()

    def test_profile_string_representation(self):
        """Verifies the __str__ method returns the expected format."""
        self.assertEqual(str(self.user.profile), "Profile for +2399912345")

    def test_whatsapp_link_generation_clean(self):
        """Tests that whatsapp_link sanitizes clean mobile numbers."""
        self.assertEqual(self.user.profile.whatsapp_link, "https://wa.me/2399912345")

    def test_whatsapp_link_removes_leading_zero(self):
        """Tests that a leading zero is cleanly removed via removeprefix."""
        self.user.mobile_number = "+02399912345"
        self.user.save()
        self.assertEqual(self.user.profile.whatsapp_link, "https://wa.me/2399912345")


class CategoryModelTest(TestCase):
    def test_category_creation_and_string_representation(self):
        """Ensures subcategories link correctly and custom emojis render."""
        parent_cat = Category.objects.create(
            name="Eletrónicos", slug="eletronicos", icon="💻"
        )
        child_cat = Category.objects.create(
            name="Telemóveis", slug="telemoveis", parent=parent_cat
        )

        self.assertEqual(str(parent_cat), "💻 Eletrónicos")
        self.assertEqual(str(child_cat), "📁 Telemóveis")
        self.assertIn(child_cat, parent_cat.subcategories.all())


class AdModelTest(TestCase):
    def setUp(self):
        self.user = create_new_valid_user()
        self.user.save()
        self.category = Category.objects.create(name="Imóveis", slug="imoveis")

    def test_default_expiration_date(self):
        """Validates the expiration helper returns a timeframe 7 days away."""
        now = timezone.now()
        expr = default_expiration_date()
        self.assertTrue(
            now + timedelta(days=6, hours=23) < expr < now + timedelta(days=7, hours=1)
        )

    def test_ad_creation_defaults(self):
        """Validates standard defaults such as active status and pricing structures."""
        ad = Ad.objects.create(
            customer=self.user.profile,
            category=self.category,
            product_name="Casa de Praia",
            price=Decimal("1500.00"),
        )
        self.assertEqual(ad.status, AdStatus.ACTIVE)
        self.assertEqual(ad.condition, AdCondition.NEW)
        self.assertFalse(ad.is_featured)
        self.assertEqual(str(ad), "Casa de Praia - +2399912345")

    def test_is_expired_method(self):
        """Validates if expired ads correctly mark themselves."""
        ad = Ad.objects.create(
            customer=self.user.profile,
            product_name="Item Antigo",
            expires_at=timezone.now() - timedelta(hours=1),
        )
        self.assertTrue(ad.is_expired())

    def test_save_method_updates_status_on_expiration(self):
        """Ensures saving an expired ad auto-updates its state to EXPIRED."""
        ad = Ad.objects.create(
            customer=self.user.profile,
            product_name="Expirado",
            expires_at=timezone.now() - timedelta(days=1),
        )
        # Check that override logic triggers status transition
        self.assertEqual(ad.status, AdStatus.EXPIRED)


class TemporaryAdModelTest(TestCase):
    def setUp(self):
        self.user = create_new_valid_user()
        self.user.save()
        self.category = Category.objects.create(name="Moda", slug="moda")

        # 1. Create a genuine tiny image in memory using Pillow
        buffer = BytesIO()
        # A tiny 10x10 white square image is enough for testing
        img = Image.new("RGB", (10, 10), color="white")
        img.save(buffer, format="JPEG")
        buffer.seek(0)

        # 2. Assign the valid raw image bytes into the SimpleUploadedFile
        self.mock_image = SimpleUploadedFile(
            name="test_image.jpg", 
            content=buffer.read(), 
            content_type="image/jpeg"
        )

    def test_transfer_to_official_ad_success(self):
        """Verifies migration paths from guest workflows to formal accounts."""
        temp_ad = TemporaryAd.objects.create(
            product_name="T-Shirt",
            description="Nice cotton shirt",
            price=Decimal("250.00"),
            category=self.category,
        )
        TemporaryAdImage.objects.create(
            temporary_ad=temp_ad, image=self.mock_image, caption="Front View", order=1
        )

        # Action: Migrating production records
        official_ad = temp_ad.transfer_to_official_ad(self.user.profile)

        # Assertions for main ad structure
        self.assertEqual(Ad.objects.count(), 1)
        self.assertEqual(official_ad.product_name, "T-Shirt")
        self.assertEqual(official_ad.customer, self.user.profile)
        self.assertEqual(official_ad.category, self.category)

        # Assertions for image translations
        self.assertEqual(AdImage.objects.count(), 1)
        migrated_img = AdImage.objects.first()
        self.assertEqual(migrated_img.ad, official_ad)
        self.assertEqual(migrated_img.caption, "Front View")

        # Assertions ensuring clean garbage collections
        self.assertFalse(TemporaryAd.objects.filter(id=temp_ad.id).exists())

    def test_transfer_to_official_ad_invalid_profile(self):
        """Throws explicit ValidationErrors if user data structures are corrupt."""
        temp_ad = TemporaryAd.objects.create(product_name="Error Test")

        with self.assertRaises(ValidationError):
            temp_ad.transfer_to_official_ad(None)

        with self.assertRaises(ValidationError):
            temp_ad.transfer_to_official_ad("not-a-profile-instance")
