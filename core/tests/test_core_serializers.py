# from rest_framework.test import APISimpleTestCase
import pytest

from core.serializers import UserCreateSerializer


@pytest.fixture
def user_valid_data():
    return {"mobile_number": "+2399882053", "district": "AGUA_GRANDE"}


@pytest.mark.django_db
class TestCoreSerializers:
    def test_user_registration_success(self, user_valid_data):
        # Given
        user_data = user_valid_data
        # Act
        serializer = UserCreateSerializer(data=user_data)
        # Then
        assert serializer.is_valid()

    def test_user_registration_non_code_number(self, user_valid_data):
        # Given
        user_data = user_valid_data
        user_data["mobile_number"] = "9882053"
        # Act
        serializer = UserCreateSerializer(data=user_data)
        # Then
        assert not serializer.is_valid()

    def test_user_registration_non_data(self):
        # Given
        user_data = {}
        # Act
        serializer = UserCreateSerializer(data=user_data)
        # Then
        assert not serializer.is_valid()
