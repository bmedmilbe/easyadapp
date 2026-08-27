import uuid
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from ads.models import Ad, Category, TemporaryAd, TemporaryAdImage
from ads.serializers import (
    AdCreateSerializer,
    CategorySerializer,
    CustomerProfileSerializer,
    TemporaryAdImageSerializer,
)

User = get_user_model()

def create_image_using_bytes_io(name="test_image.jpg"):
    # 1. Create a genuine tiny image in memory using Pillow
    buffer = BytesIO()
    # A tiny 10x10 white square image is enough for testing
    img = Image.new("RGB", (10, 10), color="white")
    img.save(buffer, format="JPEG")
    buffer.seek(0)

    # 2. Assign the valid raw image bytes into the SimpleUploadedFile
    return SimpleUploadedFile(
        name=name, 
        content=buffer.read(), 
        content_type="image/jpeg"
    )
class CustomerProfileSerializerTest(TestCase):
    def setUp(self):
        # Setup modern Django custom user profile fields mocked in serializer source
        self.user = User.objects.create_user(
            username="profuser",
            password="pwd",
            mobile_number="+239995555",
            district="AGUA_GRANDE",
        )
        self.user.save()

    def test_customer_profile_read_only_source_fields(self):
        """Validates nested source lookups read data successfully across dependencies."""
        serializer = CustomerProfileSerializer(instance=self.user.profile)
        data = serializer.data

        self.assertEqual(data["mobile_number"], "+239995555")
        self.assertEqual(data["whatsapp_link"], "https://wa.me/239995555")


class CategorySerializerTest(TestCase):
    def test_category_serialization_output(self):
        """Verifies serialiser fields structure matching model definition metadata."""
        category = Category.objects.create(
            name="Carros", slug="carros", icon="🚗", description="Auto"
        )
        serializer = CategorySerializer(instance=category)

        self.assertEqual(serializer.data["name"], "Carros")
        self.assertEqual(serializer.data["slug"], "carros")


class TemporaryAdImageSerializerTest(TestCase):
    def test_create_injects_context_temp_ad_id(self):
        """Validates contextual field injection routing during file ingestion stages."""
        category = Category.objects.create(name="Outros", slug="outros")
        temp_ad = TemporaryAd.objects.create(product_name="Draft", category=category)

        
        mock_file = create_image_using_bytes_io()

       
        data = {"image": mock_file, "caption": "Side profile", "order": 1}

        serializer = TemporaryAdImageSerializer(
            data=data, context={"temp_ad_id": temp_ad.id}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        img_instance = serializer.save()
        self.assertEqual(img_instance.temporary_ad_id, temp_ad.id)


class AdCreateSerializerValidationTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.category = Category.objects.create(name="Livros", slug="livros")
        self.user = User.objects.create_user(
            username="profuser2",
            password="pwd2",
            mobile_number="+2399955552",
            district="AGUA_GRANDE",
        )
        self.user.save()

        # Base healthy draft asset
        self.temp_ad = TemporaryAd.objects.create(
            product_name="Dicionário", category=self.category, price=Decimal("150.00")
        )
        # Mock file reference to satisfy standard minimum imaging compliance validations
        self.mock_file = create_image_using_bytes_io()        
        TemporaryAdImage.objects.create(temporary_ad=self.temp_ad, image=self.mock_file)

    def test_validation_passes_for_complete_draft(self):
        """Ensures fully compliant guest payloads validate successfully."""
        data = {"temp_ad_id": str(self.temp_ad.id)}
        serializer = AdCreateSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["temp_ad_id"], self.temp_ad.id)

    def test_validation_fails_non_existent_uuid(self):
        """Throws 400 error states when matching identifiers cannot be located."""
        data = {"temp_ad_id": str(uuid.uuid4())}
        serializer = AdCreateSerializer(data=data)

        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Temp AD not found!", context.exception.detail["detail"])

    def test_validation_fails_missing_product_name(self):
        """Catches empty records before execution pipelines receive data."""
        self.temp_ad.product_name = ""
        self.temp_ad.save()

        serializer = AdCreateSerializer(data={"temp_ad_id": str(self.temp_ad.id)})
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn(
            "Temp AD or product name not found!", context.exception.detail["detail"]
        )

    def test_validation_fails_missing_category(self):
        """Enforces schema consistency rules for categorisation systems."""
        self.temp_ad.category = None
        self.temp_ad.save()

        serializer = AdCreateSerializer(data={"temp_ad_id": str(self.temp_ad.id)})
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("category", context.exception.detail)

    def test_validation_fails_invalid_price(self):
        """Blocks zero value setups or missing valuation matrix components."""
        self.temp_ad.price = Decimal("0.00")
        self.temp_ad.save()

        serializer = AdCreateSerializer(data={"temp_ad_id": str(self.temp_ad.id)})
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("price", context.exception.detail)

    def test_validation_fails_missing_images(self):
        """Enforces application workflow rules requiring asset verification images."""
        self.temp_ad.temporary_images.all().delete()

        serializer = AdCreateSerializer(data={"temp_ad_id": str(self.temp_ad.id)})
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("images", context.exception.detail)


class AdCreateSerializerCreationTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.category = Category.objects.create(name="Jogos", slug="jogos")
        self.user = User.objects.create_user(
            username="gamer",
            password="pwd",
            mobile_number="+2399955552",
            district="AGUA_GRANDE",
        )
        self.user.save()

        self.temp_ad = TemporaryAd.objects.create(
            product_name="Consola PS5",
            category=self.category,
            price=Decimal("9000.00"),
            description="Consola PS5 Description",
        )
        
        self.mock_file = create_image_using_bytes_io()
        TemporaryAdImage.objects.create(temporary_ad=self.temp_ad, image=self.mock_file)

    def test_create_fails_if_unauthenticated(self):
        """Refuses conversion workflows when context lacks authentication states."""
        request = self.factory.post("/api/ads/")  # Anonymous user by default

        serializer = AdCreateSerializer(
            data={"temp_ad_id": str(self.temp_ad.id)}, context={"request": request}
        )
        serializer.is_valid()

        with self.assertRaises(ValidationError) as context:
            serializer.save()
        self.assertIn("Authentication required.", context.exception.detail["detail"])

    def test_create_fails_if_profile_does_not_exist(self):
        """Fails gracefully if authenticated identity lacks matching application profiles."""

        serializer = AdCreateSerializer(
            data={"temp_ad_id": str(self.temp_ad.id)}, context={"customer_id": 99}
        )
        serializer.is_valid()

        with self.assertRaises(ValidationError) as context:
            serializer.save()
        self.assertIn("User profile not found.", context.exception.detail["detail"])

    def test_create_success_with_valid_context(self):
        """Validates end-to-end user-bound promotions from temporary records."""

        serializer = AdCreateSerializer(
            data={"temp_ad_id": str(self.temp_ad.id)},
            context={"customer_id": self.user.profile.id},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        official_ad = serializer.save()

        self.assertIsInstance(official_ad, Ad)
        self.assertEqual(official_ad.product_name, "Consola PS5")
        self.assertEqual(Ad.objects.count(), 1)
