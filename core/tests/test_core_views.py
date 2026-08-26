from rest_framework import status
from rest_framework.test import APITestCase

from core.models import User


class TestCoreViews(APITestCase):
    def setUp(self):
        self.register_url = "/api/auth/users/"
        self.login_url = "/api/auth/jwt/create/"
        self.valid_data = {
            "mobile_number": "+2399882053",
            "password": "securepassword123",
            "district": "AGUA_GRANDE",
        }

    def test_core_api_create_account(self):
        """Ensure we can create a new account object and verify DB state."""
        response = self.client.post(self.register_url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

        # Verify response matches sent payload (ignoring password which shouldn't be returned raw)
        self.assertEqual(
            response.data["mobile_number"], self.valid_data["mobile_number"]
        )

        # Verify database fields
        user = User.objects.get()
        self.assertEqual(user.username, "+2399882053")
        self.assertEqual(user.mobile_number, "+2399882053")
        self.assertEqual(user.district, "AGUA_GRANDE")

    def test_create_account_duplicate_mobile_number(self):
        """Ensure a user cannot register with an existing mobile number."""
        # Create initial user
        User.objects.create_user(
            **self.valid_data,
            username=self.valid_data["mobile_number"],
        )

        # Try to register again with same data
        response = self.client.post(self.register_url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)  # No new user added

    def test_login_success(self):
        """Ensure an existing user can log in with correct credentials."""
        # Pre-create the user in the database
        User.objects.create_user(
            **self.valid_data,
            username=self.valid_data["mobile_number"],
        )

        # Login payload matching what your backend expects (usually username or mobile_number)
        login_data = {
            "mobile_number": self.valid_data["mobile_number"],
            "password": self.valid_data["password"],
        }

        response = self.client.post(self.login_url, login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify an auth token or access token is returned
        self.assertIn("access", response.data)  # Change to "access" if using Simple JWT

    def test_login_invalid_credentials(self):
        """Ensure login fails with wrong password."""
        User.objects.create_user(
            **self.valid_data,
            username=self.valid_data["mobile_number"],
        )

        invalid_login_data = {
            "username": self.valid_data["mobile_number"],
            "password": "wrongpassword",
        }

        response = self.client.post(self.login_url, invalid_login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("access", response.data)
