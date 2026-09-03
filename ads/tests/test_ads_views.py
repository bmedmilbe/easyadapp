import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from ads.tests.factories import (
    AdFactory,
    AdImageFactory,
    AdTempFactory,
    CategoryFactoryChild,
    CategoryFactoryFather,
    TemporaryAdImageFactory,
    UserFactory,
    genarate_image,
)
from ads.views import (
    AdImageViewSet,
    AdManageViewSet,
    AdViewViewSet,
    CategoryViewSet,
    TemporaryAdImageViewSet,
    TemporaryAdViewSet,
)

User = get_user_model()


# ==========================================
# TEST CASES
# ==========================================


@pytest.mark.django_db
class TestCategoryViewSet:
    """Tests the read-only, publicly accessible CategoryViewSet endpoints."""

    def test_list_categories_publicly(self):
        factory = APIRequestFactory()
        category = CategoryFactoryFather()
        url = reverse("ads:category-list")
        view = CategoryViewSet.as_view({"get": "list"})

        request = factory.get(url)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["slug"] == category.slug

    def test_retrieve_category_by_slug(self):
        factory = APIRequestFactory()
        category = CategoryFactoryChild()
        url = reverse("ads:category-detail", kwargs={"slug": category.slug})
        view = CategoryViewSet.as_view({"get": "retrieve"})
        request = factory.get(url)
        response = view(request, slug=category.slug)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == category.name


@pytest.mark.django_db
class TestAdViewViewSet:
    """Tests the read-only, publicly accessible AdViewViewSet listing."""

    def test_list_ads_publicly(self):
        factory = APIRequestFactory()
        AdFactory(product_name="a")
        AdFactory(product_name="b")
        url = reverse("ads:ad-view-list")
        view = AdViewViewSet.as_view({"get": "list"})

        request = factory.get(url)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_retrieve_single_ad_publicly(self):
        factory = APIRequestFactory()
        ad = AdFactory(product_name="b")
        url = reverse("ads:ad-view-detail", kwargs={"pk": ad.pk})
        view = AdViewViewSet.as_view({"get": "retrieve"})

        request = factory.get(url)
        response = view(request, pk=ad.pk)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["product_name"] == ad.product_name


@pytest.mark.django_db
class TestAdManageViewSet:
    """Tests mutating actions and permission isolation rules on AdManageViewSet."""

    def test_anonymous_user_cannot_mutate(self):
        factory = APIRequestFactory()
        url = reverse("ads:ad-manage-list")
        request = factory.post(url, data={})
        view = AdManageViewSet.as_view({"post": "create"})
        response = view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_user_can_create_ad(self):

        factory = APIRequestFactory()
        user = UserFactory()
        temp_ad = AdTempFactory()
        TemporaryAdImageFactory(temporary_ad=temp_ad)
        url = reverse("ads:ad-manage-list")
        payload = {"temp_ad_id": str(temp_ad.id)}

        request = factory.post(url, data=payload)
        force_authenticate(request, user=user)
        view = AdManageViewSet.as_view({"post": "create"})
        response = view(request)

        assert response.status_code == status.HTTP_201_CREATED

    def test_queryset_isolation_prevents_viewing_others_ads(self):
        """Validates get_queryset filters out ads not belonging to the authenticated profile."""

        factory = APIRequestFactory()
        user_a = UserFactory()
        user_b = UserFactory(mobile_number="+2399912445")
        ad = AdFactory(customer__user=user_b)
        url_detail = reverse("ads:ad-manage-detail", kwargs={"pk": ad.pk})

        views = AdManageViewSet.as_view({"get": "retrieve"})

        request_a = factory.get(url_detail)
        force_authenticate(request_a, user=user_a)
        response_a = views(request_a, pk=ad.pk)

        request_b = factory.get(url_detail)
        force_authenticate(request_b, user=user_b)
        response_b = views(request_b, pk=ad.pk)

        assert response_a.status_code == status.HTTP_404_NOT_FOUND
        assert response_b.status_code == status.HTTP_200_OK

    def test_user_cannot_modify_or_delete_others_ads(self):
        factory = APIRequestFactory()
        user_a = UserFactory()
        user_b = UserFactory(mobile_number="+2399912445")
        ad = AdFactory(customer__user=user_b)
        url_detail = reverse("ads:ad-manage-detail", kwargs={"pk": ad.pk})

        views_put = AdManageViewSet.as_view({"put": "update"})

        request_put = factory.put(url_detail, data={"product_name": "Hacked Title"})
        force_authenticate(request_put, user=user_a)
        response_put = views_put(request_put, pk=ad.pk)

        views_delete = AdManageViewSet.as_view({"delete": "destroy"})
        request_delete = factory.delete(url_detail)
        force_authenticate(request_delete, user=user_a)
        response_delete = views_delete(request_delete, pk=ad.pk)

        assert response_put.status_code == status.HTTP_404_NOT_FOUND
        assert response_delete.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAdImageViewSet:
    """Tests nested routing endpoints (/ads/{ad_pk}/images/) for verified ads."""

    def test_list_nested_images_publicly(self):
        factory = APIRequestFactory()
        ad = AdFactory()
        AdImageFactory(ad=ad)

        url = reverse("ads:ad-image-list", kwargs={"ad_pk": ad.pk})
        request = factory.get(url)

        view = AdImageViewSet.as_view({"get": "list"})

        response = view(request, ad_pk=ad.pk)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_anonymous_user_cannot_upload_ad_image(self):
        factory = APIRequestFactory()
        ad = AdFactory()
        url = reverse("ads:ad-image-list", kwargs={"ad_pk": ad.pk})
        view = AdImageViewSet.as_view({"post": "create"})

        request = factory.post(url, data={"image": genarate_image()})

        response = view(request, ad_pk=ad.pk)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTemporaryAdViewSet:
    """Tests the limited POST and GET-Detail actions for the guest temporary flow."""

    def test_guest_can_create_temporary_ad(self):
        factory = APIRequestFactory()
        url = reverse("ads:temporary-ad-list")
        view = TemporaryAdViewSet.as_view({"post": "create"})

        payload = {
            "product_name": "Anonymous Couch",
            "description": "Moving out sale",
            "price": 100.00,
        }
        request = factory.post(url, data=payload)

        response = view(request)
        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.data

    def test_guest_can_retrieve_temporary_ad(self):
        factory = APIRequestFactory()
        ad = AdTempFactory()
        url = reverse("ads:temporary-ad-detail", kwargs={"pk": ad.pk})
        view = TemporaryAdViewSet.as_view({"get": "retrieve"})

        request = factory.get(url)
        response = view(request, pk=ad.pk)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["product_name"] == ad.product_name


@pytest.mark.django_db
class TestTemporaryAdImageViewSet:
    """Tests the completely unauthenticated nested routes for temporary ad photos."""

    def test_anonymous_user_can_upload_temporary_ad_image(self):
        factory = APIRequestFactory()
        temporary_ad = AdTempFactory()
        url = reverse(
            "ads:temporary-ad-image-list",
            kwargs={"temporary_ad_pk": str(temporary_ad.pk)},
        )

        payload = {
            "image": genarate_image(),
            "caption": "Test Guest Upload",
            "order": 1,
        }
        view = TemporaryAdImageViewSet.as_view({"post": "create"})

        request = factory.post(url, data=payload, format="multipart")
        response = view(request, temporary_ad_pk=temporary_ad.pk)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["caption"] == "Test Guest Upload"

    def test_list_nested_temporary_images(self):
        factory = APIRequestFactory()
        temporary_ad = AdTempFactory()
        TemporaryAdImageFactory(temporary_ad=temporary_ad)

        url = reverse(
            "ads:temporary-ad-image-list", kwargs={"temporary_ad_pk": temporary_ad.pk}
        )
        view = TemporaryAdImageViewSet.as_view({"get": "list"})

        request = factory.get(url)

        response = view(request, temporary_ad_pk=temporary_ad.pk)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
