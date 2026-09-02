from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from ads.models import (
    AdCondition,
    AdStatus,
    TemporaryAd,
    TemporaryAdImage,
    default_expiration_date,
)
from ads.tests.factories import (
    AdFactory,
    AdTempFactory,
    CategoryFactoryChild,
    CategoryFactoryFather,
    CustomerProfileFactory,
    TemporaryAdImageFactory,
    UserFactory,
)

User = get_user_model()

class CustomerProfileModelTest(TestCase):
    
    def test_profile_string_representation(self):
        """Verifies the __str__ method returns the expected format."""
        #Arrange and #Act
        customer = CustomerProfileFactory.build()
        #Assert
        self.assertEqual(str(customer), f"Profile for {customer.user.mobile_number}")
        self.assertEqual(customer.whatsapp_link, f"https://wa.me/{customer.user.mobile_number}".replace("+",""))

    def test_whatsapp_link_removes_leading_zero(self):
        """Tests that a leading zero is cleanly removed via removeprefix."""
        user = UserFactory(mobile_number="+02573687638")
        customer = CustomerProfileFactory.build(user=user)
        self.assertEqual(customer.whatsapp_link, "https://wa.me/2573687638")


class CategoryModelTest(TestCase):
    def test_category_creation_and_string_representation(self):
        """Ensures subcategories link correctly and custom emojis render."""
        parent_cat = CategoryFactoryFather()

        child_cat = CategoryFactoryChild(parent=parent_cat)

        self.assertEqual(str(parent_cat), f"{parent_cat.icon} {parent_cat.name}")
        self.assertEqual(str(child_cat), f"{child_cat.icon} {child_cat.name}")
        self.assertIn(child_cat, parent_cat.subcategories.all())


class AdModelTest(TestCase):
    
    def test_default_expiration_date(self):
        """Validates the expiration helper returns a timeframe 7 days away."""
        now = timezone.now()
        expr = default_expiration_date()
        self.assertTrue(
            now + timedelta(days=6, hours=23) < expr < now + timedelta(days=7, hours=1)
        )

    def test_ad_creation_defaults(self):
        """Validates standard defaults such as active status and pricing structures."""
        user = UserFactory(mobile_number="+2399912345")
        customer = CustomerProfileFactory(user=user)
        ad = AdFactory.build(customer=customer,product_name="Casa de Praia")
        self.assertEqual(ad.status, AdStatus.ACTIVE)
        self.assertEqual(ad.condition, AdCondition.NEW)
        self.assertFalse(ad.is_featured)
        self.assertEqual(str(ad), "Casa de Praia - +2399912345")

    def test_is_expired_method(self):
        """Validates if expired ads correctly mark themselves."""
        ad = AdFactory.build(
            expires_at=timezone.now() - timedelta(hours=1),
        )
        self.assertTrue(ad.is_expired())


class TemporaryAdModelTest(TestCase):
    
    def test_transfer_to_official_ad_success(self):
        """Verifies migration paths from guest workflows to formal accounts."""
        # Arrange
        temp_ad = AdTempFactory(product_name="T-Shirt")
        original_img = TemporaryAdImageFactory(temporary_ad=temp_ad, caption="Front View")
        customer = CustomerProfileFactory()

        # Act
        official_ad = temp_ad.transfer_to_official_ad(customer)

        # Assertions for main ad structure
        self.assertIsNotNone(official_ad)
        self.assertEqual(official_ad.product_name, "T-Shirt")
        self.assertEqual(official_ad.customer, customer)
        self.assertEqual(official_ad.category, temp_ad.category)

        # Assertions for image translations
        self.assertEqual(official_ad.images.count(), 1)
        new_img = official_ad.images.first()
        self.assertEqual(new_img.caption, "Front View")

        # Assertions ensuring clean garbage collections
        self.assertFalse(TemporaryAd.objects.filter(id=temp_ad.id).exists())
        self.assertFalse(TemporaryAdImage.objects.filter(id=original_img.id).exists())

    def test_transfer_to_official_ad_invalid_profile(self):
        """Throws explicit ValidationErrors if user data structures are corrupt."""
        temp_ad = AdTempFactory.build(product_name="Error Test")

        with self.assertRaises(ValidationError):
            temp_ad.transfer_to_official_ad(None)

        with self.assertRaises(ValidationError):
            temp_ad.transfer_to_official_ad("not-a-profile-instance")
