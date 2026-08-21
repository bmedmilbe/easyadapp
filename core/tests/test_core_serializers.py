
# from rest_framework.test import APISimpleTestCase
import pytest
from core.models import User
from core.serializers import UserLoginSerializer, UserRegistrationSerializer
from rest_framework.exceptions import AuthenticationFailed


@pytest.mark.django_db
class TestCoreSerializers:
    def test_user_registration_success(self):
        #Given
        user_data =  {
            "mobile_number":"+2399882053",
        }
        #Act
        serializer = UserRegistrationSerializer(data=user_data)
        #Then
        assert serializer.is_valid()
        assert serializer.validated_data == user_data

    def test_user_registration_non_code_number(self):
        #Given
        user_data =  {
            "mobile_number":"9882053",
        }
        #Act
        serializer = UserRegistrationSerializer(data=user_data)
        #Then
        assert not serializer.is_valid()

    def test_user_registration_non_data(self):
            #Given
            user_data =  {}
            #Act
            serializer = UserRegistrationSerializer(data=user_data)
            #Then
            assert not serializer.is_valid()





@pytest.mark.django_db
class TestUserLoginSerializer:
    def test_user_login_success(self):
        # Given: A registered user in the database
        mobile = "+2399882053"
        pin = "1234"
        User.objects.create_user(mobile_number=mobile, pin=pin, username=mobile)

        login_data = {
            "mobile_number": mobile,
            "password": pin
        }

        # Act
        serializer = UserLoginSerializer(data=login_data)
        
        # Then
        assert serializer.is_valid()
        assert 'access' in serializer.validated_data
        assert 'refresh' in serializer.validated_data

    def test_user_login_non_code_number(self):
        # Given
        login_data = {
            "mobile_number": "9882053",
            "password": "1234"
        }

        # Act
        serializer = UserLoginSerializer(data=login_data)

        # Then
        assert not serializer.is_valid()
        assert 'mobile_number' in serializer.errors


    def test_user_login_wrong_credentials(self):
        # Given: User exists, but login data uses the wrong PIN
        mobile = "+2399882053"
        User.objects.create_user(mobile_number=mobile, pin="1234", username=mobile)

        login_data = {
            "mobile_number": mobile,
            "password": "9999"  # Incorrect PIN
        }

        # Act & Then: SimpleJWT serializers raise AuthenticationFailed during validation
        serializer = UserLoginSerializer(data=login_data)
        with pytest.raises(AuthenticationFailed):
            serializer.is_valid(raise_exception=True)

    def test_user_login_missing_data(self):
        # Given
        login_data = {}

        # Act
        serializer = UserLoginSerializer(data=login_data)

        # Then
        assert not serializer.is_valid()

