from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory

from ads.models import (
    Ad,
    AdImage,
    Category,
    TemporaryAd,
    TemporaryAdImage,
)

User = get_user_model()
User = get_user_model()

# ==========================================
# FIXTURES
# ==========================================


@pytest.fixture
def api_client():
    """Provides a standard unauthenticated DRF API client."""
    return APIClient()


@pytest.fixture
def create_user(django_user_model):
    """Factory fixture to quickly spin up testing users."""

    def make_user(
        username="testuser",
        password="password123",
        mobile_number="+239995555",
        district="AGUA_GRANDE",
    ):
        return django_user_model.objects.create_user(
            username=username,
            password=password,
            mobile_number=mobile_number,
            district=district,
        )

    return make_user


@pytest.fixture
def customer_profile(create_user):
    """Creates a regular testing user accompanied by a profile."""
    user = create_user(
        username="customer_user",
        password="password123",
        mobile_number="+239995555",
        district="AGUA_GRANDE",
    )
    return user.profile


@pytest.fixture
def other_customer_profile(create_user):
    """Creates an isolated second profile to test query separation."""
    user = create_user(
        username="other_user",
        password="password223",
        mobile_number="+239994555",
        district="AGUA_GRANDE",
    )
    return user.profile


@pytest.fixture
def category():
    """Generates a test Category."""
    return Category.objects.create(name="Electronics", slug="electronics")


@pytest.fixture
def official_ad(customer_profile, category):
    """Generates an Ad owned by the primary customer profile."""
    return Ad.objects.create(
        customer_id=customer_profile.id,
        category=category,
        product_name="iPhone 15",
        description="Like new",
        price=999.00,
        status="active",
        condition="used",
    )


@pytest.fixture
def other_ad(other_customer_profile, category):
    """Generates an Ad owned by a competing profile."""
    return Ad.objects.create(
        customer_id=other_customer_profile.id,
        category=category,
        product_name="Samsung S24",
        description="Sealed box",
        price=899.00,
        status="active",
        condition="new",
    )


@pytest.fixture
def temporary_ad():
    """Generates an unauthenticated guest TemporaryAd."""
    return TemporaryAd.objects.create(
        product_name="Guest Laptop", description="Quick Sale", price=450.00
    )


# ==========================================
# TEST CASES
# ==========================================


@pytest.mark.django_db
class TestCategoryViewSet:
    """Tests the read-only, publicly accessible CategoryViewSet endpoints."""

    def test_list_categories_publicly(self, api_client, category):
        url = reverse("ads:category-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["slug"] == category.slug

    def test_retrieve_category_by_slug(self, api_client, category):
        url = reverse("ads:category-detail", kwargs={"slug": category.slug})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == category.name


@pytest.mark.django_db
class TestAdViewViewSet:
    """Tests the read-only, publicly accessible AdViewViewSet listing."""

    def test_list_ads_publicly(self, api_client, official_ad, other_ad):
        url = reverse("ads:ad-view-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # Public listings must yield all instances across users
        assert len(response.data["results"]) == 2

    def test_retrieve_single_ad_publicly(self, api_client, official_ad):
        url = reverse("ads:ad-view-detail", kwargs={"pk": official_ad.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["product_name"] == official_ad.product_name


@pytest.mark.django_db
class TestAdManageViewSet:
    """Tests mutating actions and permission isolation rules on AdManageViewSet."""

    @pytest.fixture(autouse=True)
    def setup_method_data(self):
        """
        Replaces __init__ setup. Runs automatically before every test method
        providing the isolated database state required.
        """
        self.factory = APIRequestFactory()
        self.category = Category.objects.create(name="Livros", slug="livros")

        # Ensure your custom User model has mobile_number field handled cleanly
        self.user = User.objects.create_user(
            username="profuser2",
            password="pwd2",
            mobile_number="+2399955552",
            district="AGUA_GRANDE",
        )

        # Base healthy draft asset
        self.temp_ad = TemporaryAd.objects.create(
            product_name="Dicionário",
            category=self.category,
            price=Decimal("150.00"),
            description="Dicionario text",
        )

        # Mock file reference to satisfy standard minimum imaging compliance validations
        self.mock_file = SimpleUploadedFile("b.jpg", b"img", content_type="image/jpeg")
        TemporaryAdImage.objects.create(temporary_ad=self.temp_ad, image=self.mock_file)

    def test_anonymous_user_cannot_mutate(self, api_client):
        url = reverse("ads:ad-manage-list")
        response = api_client.post(url, data={})
        # Correctly updated to match your prior 401/403 verification
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_user_can_create_ad(self, api_client, customer_profile):
        api_client.force_authenticate(user=customer_profile.user)
        url = reverse("ads:ad-manage-list")

        # Using self.temp_ad built dynamically in our auto-running setup fixture
        payload = {"temp_ad_id": str(self.temp_ad.id)}
        response = api_client.post(url, data=payload)
        assert response.status_code == status.HTTP_201_CREATED

    def test_queryset_isolation_prevents_viewing_others_ads(
        self, api_client, customer_profile, other_ad
    ):
        """Validates get_queryset filters out ads not belonging to the authenticated profile."""
        api_client.force_authenticate(user=customer_profile.user)

        url_detail = reverse("ads:ad-manage-detail", kwargs={"pk": other_ad.pk})
        response = api_client.get(url_detail)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_user_cannot_modify_or_delete_others_ads(
        self, api_client, customer_profile, other_ad
    ):
        api_client.force_authenticate(user=customer_profile.user)
        url = reverse("ads:ad-manage-detail", kwargs={"pk": other_ad.pk})

        # Try updating
        response = api_client.put(url, data={"product_name": "Hacked Title"})
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Try deleting
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAdImageViewSet:
    """Tests nested routing endpoints (/ads/{ad_pk}/images/) for verified ads."""

    def test_list_nested_images_publicly(self, api_client, official_ad):
        # Create an asset attached to the official ad
        AdImage.objects.create(ad=official_ad, image="ads/test.jpg")

        url = reverse("ads:ad-image-list", kwargs={"ad_pk": official_ad.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_anonymous_user_cannot_upload_ad_image(self, api_client, official_ad):
        url = reverse("ads:ad-image-list", kwargs={"ad_pk": official_ad.pk})
        response = api_client.post(url, data={"image": "new_image.png"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTemporaryAdViewSet:
    """Tests the limited POST and GET-Detail actions for the guest temporary flow."""

    def test_guest_can_create_temporary_ad(self, api_client):
        url = reverse("ads:temporary-ad-list")
        payload = {
            "product_name": "Anonymous Couch",
            "description": "Moving out sale",
            "price": 100.00,
        }
        response = api_client.post(url, data=payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.data

    def test_guest_can_retrieve_temporary_ad(self, api_client, temporary_ad):
        url = reverse("ads:temporary-ad-detail", kwargs={"pk": temporary_ad.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["product_name"] == temporary_ad.product_name


@pytest.mark.django_db
@pytest.mark.django_db
class TestTemporaryAdImageViewSet:
    """Tests the completely unauthenticated nested routes for temporary ad photos."""

    def test_anonymous_user_can_upload_temporary_ad_image(
        self, api_client, temporary_ad
    ):
        # 1. Reverse the URL using the temporary_ad's true UUID primary key string
        url = reverse(
            "ads:temporary-ad-image-list",
            kwargs={"temporary_ad_pk": str(temporary_ad.pk)},
        )

        # 2. Build a valid, small, in-memory mock image payload to satisfy models.ImageField
        small_gif_bytes = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00"
            b"\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b"
        )
        mock_image = SimpleUploadedFile(
            name="guest_photo.gif", content=small_gif_bytes, content_type="image/gif"
        )

        payload = {"image": mock_image, "caption": "Test Guest Upload", "order": 1}

        # 3. Post the multi-part form data to your API endpoint
        response = api_client.post(url, data=payload, format="multipart")

        # Assertions
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["caption"] == "Test Guest Upload"

    def test_list_nested_temporary_images(self, api_client, temporary_ad):
        TemporaryAdImage.objects.create(
            temporary_ad=temporary_ad, image="guest/img.png"
        )

        url = reverse(
            "ads:temporary-ad-image-list", kwargs={"temporary_ad_pk": temporary_ad.pk}
        )
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
