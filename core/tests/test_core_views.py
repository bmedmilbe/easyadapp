import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.models import User
from core.tests.factories import UserFactory


@pytest.mark.django_db
class TestCoreViews:
    def test_core_api_create_account(self):
        # Given
        factory = APIRequestFactory()
        url = reverse("user-list")
        data = {
            "mobile_number": "+2399882053",
            "password": "securepassword123",
            "district": "AGUA_GRANDE",
            "username": "+2399882053",
        }
        
        # Act
        request = factory.post(url, data=data, format="json")
        from djoser.views import UserViewSet
        view = UserViewSet.as_view({"post": "create"})
        response = view(request)

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.count() == 1
        assert response.data["mobile_number"] == data["mobile_number"]

        user = User.objects.get()
        assert user.username == "+2399882053"
        assert user.mobile_number == "+2399882053"
        assert user.district == "AGUA_GRANDE"

    def test_create_account_duplicate_mobile_number(self):
        # Given
        factory = APIRequestFactory()
        url = reverse("user-list")
        
        UserFactory(mobile_number="+2399882053", username="+2399882053")
        
        data = {
            "mobile_number": "+2399882053",
            "password": "securepassword123",
            "district": "AGUA_GRANDE",
            "username": "+2399882053",
        }

        # Act
        request = factory.post(url, data=data, format="json")
        from djoser.views import UserViewSet
        view = UserViewSet.as_view({"post": "create"})
        response = view(request)

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert User.objects.count() == 1

    def test_login_success(self):
        # Given
        factory = APIRequestFactory()
        url = reverse("jwt-create")
        
        # Create user using factory
        user = UserFactory(
            mobile_number="+2399882053",
            username="+2399882053",
        )
        user.set_password("securepassword123")
        user.save()
        
        # Use 'username' field (maps to mobile_number via USERNAME_FIELD)
        login_data = {
            "mobile_number": "+2399882053",
            "password": "securepassword123",
        }

        # Act - Use SimpleJWT's TokenObtainPairView directly
        request = factory.post(url, data=login_data, format="json")
        from rest_framework_simplejwt.views import TokenObtainPairView
        view = TokenObtainPairView.as_view()
        response = view(request)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_invalid_credentials(self):
        # Given
        factory = APIRequestFactory()
        url = reverse("jwt-create")
        
        user = UserFactory(
            mobile_number="+2399882053",
            username="+2399882053",
        )
        user.set_password("securepassword123")
        user.save()
        
        invalid_login_data = {
            "mobile_number": "+2399882053",
            "password": "wrongpassword",
        }

        # Act
        request = factory.post(url, data=invalid_login_data, format="json")
        from rest_framework_simplejwt.views import TokenObtainPairView
        view = TokenObtainPairView.as_view()
        response = view(request)

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "access" not in response.data