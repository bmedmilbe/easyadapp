import re
import secrets

from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager,
)
from django.core.exceptions import ValidationError
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, mobile_number,  pin, **extra_fields):
        """
        Create and save a regular user with the given mobile number and PIN.
        """
        if not mobile_number:
            raise ValueError('The Mobile Number must be set')
        
        
        # Clean and validate mobile number
        cleaned = re.sub(r'\s+', '', mobile_number)
        if not cleaned.startswith('+'):
            raise ValueError('Mobile number must include country code (e.g., +4475836648484)')
        if not re.match(r'^\+\d{7,15}$', cleaned):
            raise ValueError('Invalid mobile number format. Use format: +4475836648484')
        
        user = self.model(
            mobile_number=cleaned,
            **extra_fields
        )
        user.set_password(pin)
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile_number, **extra_fields):
        pin = f"{secrets.randbelow(10000):04d}"
        print(pin)
        
        return self.create_user(mobile_number, pin, **extra_fields)


class User(AbstractUser):

    mobile_number = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="Mobile Number",
        help_text="Format: +4475836648484"
    )
    
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'mobile_number'
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    
    
    def clean(self):
        """Validate the mobile number format."""
        if self.mobile_number:
            cleaned = re.sub(r'\s+', '', self.mobile_number)
            if not cleaned.startswith('+'):
                raise ValidationError({'mobile_number': 'Mobile number must include country code (e.g., +4475836648484)'})
            if not re.match(r'^\+\d{7,15}$', cleaned):
                raise ValidationError({'mobile_number': 'Invalid mobile number format. Use format: +4475836648484'})
            self.mobile_number = cleaned