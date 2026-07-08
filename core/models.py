# core/models.py
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, mobile_number, district, pin, **extra_fields):
        """
        Create and save a regular user with the given mobile number, district, and PIN.
        """
        if not mobile_number:
            raise ValueError('The Mobile Number must be set')
        if not district:
            raise ValueError('The District must be set')
        if not pin:
            raise ValueError('The 4-digit PIN must be set')
        
        # Clean the mobile number to ensure consistency
        mobile_number = self.normalize_email(mobile_number)  # We'll treat mobile as the identifier
        
        user = self.model(
            mobile_number=mobile_number,
            district=district,
            **extra_fields
        )
        user.set_password(pin)  # Hash the PIN
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile_number, district, password, **extra_fields):
        """
        Create and save a superuser with the given mobile number, district, and PIN.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        # For superusers, allow bypassing some restrictions
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(mobile_number, district, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    DISTRICT_CHOICES = [
        ('AGUA_GRANDE', 'Água Grande'),
        ('CANTAGALO', 'Cantagalo'),
        ('CAUE', 'Caué'),
        ('LEMBA', 'Lembá'),
        ('LOBATA', 'Lobata'),
        ('ME_ZOCHI', 'Mé-Zóchi'),
        ('PAGUE', 'Pagué'),
        ('DIASPORA', 'Diaspora'),
    ]
    
    mobile_number = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="Mobile Number"
    )
    district = models.CharField(
        max_length=20, 
        choices=DISTRICT_CHOICES,
        verbose_name="District"
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'mobile_number'
    REQUIRED_FIELDS = ['district']  # Required for createsuperuser
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.mobile_number
    
    def get_full_name(self):
        return self.mobile_number
    
    def get_short_name(self):
        return self.mobile_number