# core/models.py
import random
import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, phone_number, name, district, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Phone number is required')
        if not name:
            raise ValueError('Name is required')
        
        user = self.model(
            phone_number=phone_number,
            name=name,
            district=district,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, name, district, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(phone_number, name, district, password, **extra_fields)


class District(models.Model):
    name = models.CharField('Name', max_length=100, unique=True)
    code = models.CharField('Code', max_length=10, unique=True)
    is_diaspora = models.BooleanField('Is Diaspora?', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'District'
        verbose_name_plural = 'Districts'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be in format: '+239 9999999'."
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(
        'Phone Number',
        max_length=15,
        unique=True,
        validators=[phone_regex]
    )
    name = models.CharField('Full Name', max_length=255)
    district = models.ForeignKey(
        District,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='District'
    )
    
    # Authentication fields
    pin_code = models.CharField('PIN Code', max_length=6, blank=True, null=True)
    pin_created_at = models.DateTimeField('PIN Creation Date', null=True, blank=True)
    is_verified = models.BooleanField('Is Verified?', default=False)
    
    # Django standard fields
    is_active = models.BooleanField('Is Active?', default=True)
    is_staff = models.BooleanField('Is Staff?', default=False)
    is_superuser = models.BooleanField('Is Superuser?', default=False)
    last_login = models.DateTimeField('Last Login', null=True, blank=True)
    date_joined = models.DateTimeField('Date Joined', auto_now_add=True)
    
    # Tracking fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['name', 'district']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.name} ({self.phone_number})"
    
    def generate_pin(self):
        pin = str(random.randint(100000, 999999))
        self.pin_code = pin
        self.pin_created_at = timezone.now()
        self.save()
        return pin
    
    def verify_pin(self, pin):
        if not self.pin_code or not self.pin_created_at:
            return False
        
        expiration_time = self.pin_created_at + timezone.timedelta(minutes=5)
        if timezone.now() > expiration_time:
            return False
        
        return self.pin_code == pin
    
    def get_whatsapp_link(self):
        phone = self.phone_number.replace('+', '').replace(' ', '')
        return f"https://wa.me/{phone}"


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='User'
    )
    avatar = models.ImageField(
        'Avatar',
        upload_to='profiles/avatars/',
        null=True,
        blank=True
    )
    bio = models.TextField('Biography', max_length=500, blank=True)
    is_public = models.BooleanField('Is Public?', default=True)
    total_ads = models.PositiveIntegerField('Total Ads', default=0)
    active_ads = models.PositiveIntegerField('Active Ads', default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"Profile of {self.user.name}"


class SystemLog(models.Model):
    LOG_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('auth', 'Authentication'),
        ('payment', 'Payment'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
        verbose_name='User'
    )
    type = models.CharField('Type', max_length=20, choices=LOG_TYPES, default='info')
    message = models.TextField('Message')
    data = models.JSONField('Additional Data', default=dict, blank=True)
    ip_address = models.GenericIPAddressField('IP Address', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.created_at}"


class SiteConfiguration(models.Model):
    site_name = models.CharField('Site Name', max_length=100, default='MyAds')
    site_description = models.TextField('Description', blank=True)
    
    # Ad settings
    default_expiration_days = models.PositiveIntegerField('Default Expiration Days', default=30)
    max_images_per_ad = models.PositiveIntegerField('Max Images per Ad', default=10)
    free_ads_limit = models.PositiveIntegerField('Free Ads Limit', default=5)
    
    # WhatsApp
    whatsapp_business_number = models.CharField('WhatsApp Business Number', max_length=15, blank=True)
    whatsapp_message_template = models.TextField('WhatsApp Message Template', blank=True)
    
    # PIN settings
    pin_expiration_minutes = models.PositiveIntegerField('PIN Expiration (minutes)', default=5)
    
    # Highlight settings
    highlight_prices = models.JSONField('Highlight Prices', default=dict, blank=True)
    
    # Contact
    contact_email = models.EmailField('Contact Email', blank=True)
    contact_phone = models.CharField('Contact Phone', max_length=15, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site Configuration'
        verbose_name_plural = 'Site Configurations'
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        if not self.pk and SiteConfiguration.objects.exists():
            raise ValueError('A configuration already exists. Edit the existing one.')
        super().save(*args, **kwargs)


class SessionManager(models.Model):
    """Manages anonymous sessions for easyflow"""
    session_key = models.CharField('Session Key', max_length=100, unique=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions'
    )
    data = models.JSONField('Session Data', default=dict, blank=True)
    ip_address = models.GenericIPAddressField('IP Address', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    expires_at = models.DateTimeField('Expires At')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Session Manager'
        verbose_name_plural = 'Session Managers'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Session {self.session_key}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def extend_session(self, days=7):
        self.expires_at = timezone.now() + timezone.timedelta(days=days)
        self.save()