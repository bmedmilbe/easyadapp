import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from ads.models import Ad
from ads.serializers import (
    AdCreateSerializer,
    CategorySerializer,
    CustomerProfileSerializer,
    TemporaryAdImageSerializer,
)
from ads.tests.factories import (
    AdTempFactory,
    CategoryFactoryChild,
    CustomerProfileFactory,
    TemporaryAdImageFactory,
    genarate_image,
)

User = get_user_model()


class CustomerProfileSerializerTest(TestCase):
    def setUp(self):
        # Setup modern Django custom user profile fields mocked in serializer source
        self.user = User.objects.create_user(
            username="profuser",
            password="pwd",
            mobile_number="+2399912345",
            district="AGUA_GRANDE",
        )
        self.user.save()

    def test_customer_profile_read_only_source_fields(self):
        """Validates nested source lookups read data successfully across dependencies."""
        customer = CustomerProfileFactory.build()
        serializer = CustomerProfileSerializer(instance=customer)
        data = serializer.data

        self.assertEqual(data["mobile_number"], "+2399912345")
        self.assertEqual(data["whatsapp_link"], "https://wa.me/2399912345")


class CategorySerializerTest(TestCase):
    def test_category_serialization_output(self):
        """Verifies serialiser fields structure matching model definition metadata."""
        category = CategoryFactoryChild.build(name="Carros")
        serializer = CategorySerializer(instance=category)

        self.assertEqual(serializer.data["name"], "Carros")
        self.assertEqual(serializer.data["slug"], "carros")


class TemporaryAdImageSerializerTest(TestCase):
    def test_create_injects_context_temp_ad_id(self):
        """Validates contextual field injection routing during file ingestion stages."""
        temp_ad = AdTempFactory()

        data = {"image": genarate_image(), "caption": "Side profile", "order": 1}

        serializer = TemporaryAdImageSerializer(
            data=data, context={"temp_ad_id": temp_ad.id}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        img_instance = serializer.save()
        self.assertEqual(img_instance.temporary_ad_id, temp_ad.id)


class AdCreateSerializerValidationTest(TestCase):
   
    def test_validation_passes_for_complete_draft(self):
        """Ensures fully compliant guest payloads validate successfully."""

        temp_ad = AdTempFactory()
        TemporaryAdImageFactory(temporary_ad=temp_ad)
        data = {"temp_ad_id": str(temp_ad.id)}
        serializer = AdCreateSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(str(serializer.validated_data["temp_ad_id"]), temp_ad.id)

    def test_validation_fails_non_existent_uuid(self):
        """Throws 400 error states when matching identifiers cannot be located."""
        data = {"temp_ad_id": str(uuid.uuid4())}
        serializer = AdCreateSerializer(data=data)

        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Temp AD not found!", context.exception.detail["detail"])

    def test_validation_fails_missing_product_name(self):
        """Catches empty records before execution pipelines receive data."""
        
        temp_ad = AdTempFactory(product_name="")

        serializer = AdCreateSerializer(data={"temp_ad_id": str(temp_ad.id)})
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn(
            "Temp AD or product name not found!", context.exception.detail["detail"]
        )

    def test_validation_fails_missing_category(self):
        """Enforces schema consistency rules for categorisation systems."""
        
        temp_ad = AdTempFactory(category=None)

        serializer = AdCreateSerializer(data={"temp_ad_id": str(temp_ad.id)})
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("category", context.exception.detail)

    def test_validation_fails_invalid_price(self):
        """Blocks zero value setups or missing valuation matrix components."""
        
        temp_ad = AdTempFactory(price = Decimal("0.00"))

        serializer = AdCreateSerializer(data={"temp_ad_id": str(temp_ad.id)})
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("price", context.exception.detail)

    def test_validation_fails_missing_images(self):
        """Enforces application workflow rules requiring asset verification images."""
        temp_ad = AdTempFactory()
        temp_ad.temporary_images.all().delete()

        serializer = AdCreateSerializer(data={"temp_ad_id": str(temp_ad.id)})
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("images", context.exception.detail)


class AdCreateSerializerCreationTest(TestCase):
    
    def test_create_fails_if_unauthenticated(self):
        """Refuses conversion workflows when context lacks authentication states."""
        factory = APIRequestFactory()
        request = factory.post("/api/ads/")  # Anonymous user by default
        temp_ad = AdTempFactory()
        TemporaryAdImageFactory(temporary_ad=temp_ad)
        serializer = AdCreateSerializer(
            data={"temp_ad_id": str(temp_ad.id)}, context={"request": request}
        )
        serializer.is_valid()

        with self.assertRaises(ValidationError) as context:
            serializer.save()
        self.assertIn("Authentication required.", context.exception.detail["detail"])

    def test_create_fails_if_profile_does_not_exist(self):
        """Fails gracefully if authenticated identity lacks matching application profiles."""
        temp_ad = AdTempFactory()
        TemporaryAdImageFactory(temporary_ad=temp_ad)
        
        serializer = AdCreateSerializer(
            data={"temp_ad_id": str(temp_ad.id)}, context={"customer_id": 99}
        )
        self.assertTrue(serializer.is_valid())

        with self.assertRaises(ValidationError) as context:
            serializer.save()
        self.assertIn("User profile not found.", context.exception.detail["detail"])

    def test_create_success_with_valid_context(self):
        """Validates end-to-end user-bound promotions from temporary records."""
        customer = CustomerProfileFactory()
        temp_ad = AdTempFactory(product_name="Consola PS5")
        TemporaryAdImageFactory(temporary_ad=temp_ad)

        serializer = AdCreateSerializer(
            data={"temp_ad_id": str(temp_ad.id)},
            context={"customer_id": customer.id},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        official_ad = serializer.save()

        self.assertIsInstance(official_ad, Ad)
        self.assertEqual(official_ad.product_name, "Consola PS5")
        self.assertEqual(Ad.objects.count(), 1)
