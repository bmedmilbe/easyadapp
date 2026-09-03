import factory
from factory.django import DjangoModelFactory

from core.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ["mobile_number"]

    district = "AGUA_GRANDE"
    mobile_number = "+2399912345"

    username = factory.Sequence(lambda n: f"user_{n}")
    password = "password123"
