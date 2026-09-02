from io import BytesIO

import factory
import factory.fuzzy
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.utils.text import slugify
from factory.django import DjangoModelFactory
from PIL import Image

from ads.models import (
    Ad,
    Category,
    CustomerProfile,
    TemporaryAd,
    TemporaryAdImage,
)

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ["mobile_number"]

    district = "AGUA_GRANDE"
    mobile_number = "+2399912345"


    username = factory.Sequence(lambda n: f"user_{n}")
    password = "password123"

class CustomerProfileFactory(DjangoModelFactory):
    class Meta:
        model = CustomerProfile
        django_get_or_create = ["user"]

    user = factory.SubFactory(UserFactory)
    created_at = factory.Faker("date_time_this_year")
    updated_at = factory.Faker("date_time_this_year")

class CategoryFactoryFather(DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ["slug"]

    name = factory.Faker("name")
    slug = factory.LazyAttribute(lambda obj:slugify(obj.name))
    icon = factory.Faker('text', max_nb_chars=10)
    description = factory.Faker("name")
    created_at = factory.Faker("date_time_this_year")

class CategoryFactoryChild(DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ["slug"]

    name = factory.Faker("name")
    slug = factory.LazyAttribute(lambda obj:slugify(obj.name))
    icon = factory.Faker('text', max_nb_chars=10)
    description = factory.Faker("name")
    created_at = factory.Faker("date_time_this_year")
    parent = factory.SubFactory(CategoryFactoryFather)

class AdFactory(DjangoModelFactory):
    class Meta:
        model = Ad

    customer = factory.SubFactory(CustomerProfileFactory)
    category = factory.SubFactory(CategoryFactoryChild)
    product_name = factory.Faker("name")
    description = factory.Faker("name")
    price = factory.fuzzy.FuzzyDecimal(5.00, 500.00, precision=2)  
    # status = factory.fuzzy.FuzzyChoice([choice[0] for choice in AdStatus.choices])
    # condition = factory.fuzzy.FuzzyChoice([choice[0] for choice in AdCondition.choices])
    expires_at = factory.Faker("date_time_this_year", tzinfo=timezone.get_current_timezone())
    # is_featured = factory.Faker("boolean")
    created_at = factory.Faker("date_time_this_year")
    updated_at = factory.Faker("date_time_this_year")

class AdTempFactory(DjangoModelFactory):
    class Meta:
        model = TemporaryAd

    id = factory.Faker("uuid4")
    category = factory.SubFactory(CategoryFactoryChild)
    product_name = factory.Faker("name")
    description = factory.Faker("name")
    price = factory.fuzzy.FuzzyDecimal(5.00, 500.00, precision=2)  
    created_at = factory.Faker("date_time_this_year")
    updated_at = factory.Faker("date_time_this_year")

def genarate_image():
        # 1. Create a genuine tiny image in memory using Pillow
        buffer = BytesIO()
        # A tiny 10x10 white square image is enough for testing
        img = Image.new("RGB", (10, 10), color="white")
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        
        # 2. Assign the valid raw image bytes into the SimpleUploadedFile
        return SimpleUploadedFile(
            name="test_image.jpg", content=buffer.read(), content_type="image/jpeg"
        )

class TemporaryAdImageFactory(DjangoModelFactory):
    class Meta:
        model = TemporaryAdImage

    temporary_ad = factory.SubFactory(AdTempFactory)
    caption = factory.Faker("text")
    created_at = factory.Faker("date_time_this_year")
    order = factory.Sequence(lambda n: n + 1)
    image = genarate_image()
