import pytest
from django.core.exceptions import ValidationError

from core.models import User


@pytest.mark.django_db
class TestCoreModels:
    def test_create_new_user(self):
        
        # Given
        data = {
            "mobile_number": "+2399882053",
            "username": "+2399882053",
            "password": "password123",
            "district": "AGUA_GRANDE",
        }

        # Act
        saved_user = User.objects.create(**data)
        users_count = len(User.objects.all())

        # Then
        assert users_count == 1
        assert saved_user.mobile_number == data["mobile_number"]
        assert saved_user.district == data["district"]
        

    def test_create_new_user_wrong_number(self):
        # Given
        data = {"mobile_number": "9882053", "password": "password123"}

        # Act
        with pytest.raises(ValidationError):
            User.objects.create(**data)

    def test_create_new_user_no_data(self):
        # Given
        data = {}

        # Act
        with pytest.raises(ValidationError):
            User.objects.create(**data)
