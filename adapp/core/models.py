import re

from django.contrib.auth.models import (
    AbstractUser,
)
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    DISTRICT_CHOICES = [
        ("AGUA_GRANDE", "Água Grande"),
        ("MEZOCHI", "Mé-Zóchi"),
        ("LEMBA", "Lembá"),
        ("CAUE", "Cauê"),
        ("LOBATA", "Lobata"),
        ("CANTAGALO", "Cantagalo"),
        ("RAP", "Região Autonoma de Príncipe"),
        ("DIASPORA", "Diáspora"),
    ]
    district = models.CharField(max_length=255, choices=DISTRICT_CHOICES)

    mobile_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Mobile Number",
        help_text="Format: +4475836648484",
    )

    USERNAME_FIELD = "mobile_number"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.mobile_number} {self.first_name} {self.last_name}"

    def clean(self):
        """Validate the mobile number format."""
        if self.mobile_number:
            cleaned = re.sub(r"\s+", "", self.mobile_number)
            if not cleaned.startswith("+"):
                raise ValidationError(
                    {
                        "mobile_number": "Mobile number must include country code (e.g., +4475836648484)"
                    }
                )
            if not re.match(r"^\+\d{7,15}$", cleaned):
                raise ValidationError(
                    {
                        "mobile_number": "Invalid mobile number format. Use format: +4475836648484"
                    }
                )

    def save(self, *args, **kwargs):
        # self.full_clean() automatically calls self.clean()
        self.full_clean()
        super().save(*args, **kwargs)
