# ads/models.py
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField('Category Name', max_length=100, unique=True)
    slug = models.SlugField('Slug', max_length=100, unique=True)
    icon = models.CharField('Icon (FontAwesome)', max_length=50, blank=True)
    color = models.CharField('Color (hex)', max_length=7, default='#007bff')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name='Parent Category'
    )
    is_active = models.BooleanField('Is Active?', default=True)
    order = models.PositiveIntegerField('Order', default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} › {self.name}"
        return self.name
    
    @property
    def is_subcategory(self):
        return self.parent is not None


class Advertisement(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
        ('rejected', 'Rejected'),
    ]
    
    HIGHLIGHT_CHOICES = [
        ('none', 'No Highlight'),
        ('basic', 'Basic Highlight'),
        ('premium', 'Premium Highlight'),
        ('featured', 'Featured Highlight'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='advertisements',
        verbose_name='Advertiser'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='advertisements',
        verbose_name='Category'
    )
    
    title = models.CharField('Title', max_length=200)
    description = models.TextField('Description', blank=True)
    price = models.DecimalField('Price', max_digits=10, decimal_places=2, null=True, blank=True)
    is_price_negotiable = models.BooleanField('Is Price Negotiable?', default=True)
    
    # Status and visibility
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    highlight_type = models.CharField(
        'Highlight Type',
        max_length=20,
        choices=HIGHLIGHT_CHOICES,
        default='none'
    )
    views_count = models.PositiveIntegerField('Views', default=0)
    whatsapp_clicks = models.PositiveIntegerField('WhatsApp Clicks', default=0)
    
    # Dates
    created_at = models.DateTimeField('Created At', auto_now_add=True)
    updated_at = models.DateTimeField('Updated At', auto_now=True)
    published_at = models.DateTimeField('Published At', null=True, blank=True)
    expiration_date = models.DateTimeField('Expiration Date', null=True, blank=True)
    
    # EasyFlow fields
    session_key = models.CharField('Session Key', max_length=100, null=True, blank=True)
    is_anonymous = models.BooleanField('Is Anonymous?', default=True)
    temp_user_data = models.JSONField('Temporary User Data', null=True, blank=True)
    
    # Tracking
    ip_address = models.GenericIPAddressField('Creation IP', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    
    class Meta:
        verbose_name = 'Advertisement'
        verbose_name_plural = 'Advertisements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'expiration_date']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.name}"
    
    def save(self, *args, **kwargs):
        if self.status == 'active' and not self.published_at:
            self.published_at = timezone.now()
            if not self.expiration_date:
                self.expiration_date = timezone.now() + timezone.timedelta(days=30)
        
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        if self.status != 'active':
            return False
        if self.expiration_date and timezone.now() > self.expiration_date:
            self.status = 'expired'
            self.save(update_fields=['status'])
            return False
        return True
    
    @property
    def is_highlighted(self):
        return self.highlight_type != 'none'
    
    @property
    def days_remaining(self):
        if not self.expiration_date:
            return None
        delta = self.expiration_date - timezone.now()
        return max(0, delta.days)
    
    def get_whatsapp_link(self):
        return self.user.get_whatsapp_link()
    
    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def increment_whatsapp_clicks(self):
        self.whatsapp_clicks += 1
        self.save(update_fields=['whatsapp_clicks'])
    
    def assign_to_user(self, user):
        """Assign anonymous ad to a registered user"""
        self.user = user
        self.is_anonymous = False
        self.session_key = None
        self.save()
        
        # Update user profile stats
        profile = user.profile
        profile.total_ads += 1
        profile.save()


class AdvertisementImage(models.Model):
    advertisement = models.ForeignKey(
        Advertisement,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Advertisement'
    )
    image = models.ImageField('Image', upload_to='ads/images/')
    caption = models.CharField('Caption', max_length=200, blank=True)
    order = models.PositiveIntegerField('Order', default=0)
    is_primary = models.BooleanField('Is Primary?', default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Advertisement Image'
        verbose_name_plural = 'Advertisement Images'
        ordering = ['order']
        unique_together = [['advertisement', 'order']]
    
    def __str__(self):
        return f"Image {self.order} of {self.advertisement.title}"
    
    def save(self, *args, **kwargs):
        if self.is_primary:
            AdvertisementImage.objects.filter(
                advertisement=self.advertisement
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class AdvertisementView(models.Model):
    advertisement = models.ForeignKey(
        Advertisement,
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name='Advertisement'
    )
    ip_address = models.GenericIPAddressField('IP Address', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    session_key = models.CharField('Session Key', max_length=100, null=True, blank=True)
    viewed_at = models.DateTimeField('Viewed At', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Advertisement View'
        verbose_name_plural = 'Advertisement Views'
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"View of {self.advertisement.title} at {self.viewed_at}"


class AdvertisementClick(models.Model):
    advertisement = models.ForeignKey(
        Advertisement,
        on_delete=models.CASCADE,
        related_name='clicks',
        verbose_name='Advertisement'
    )
    ip_address = models.GenericIPAddressField('IP Address', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    session_key = models.CharField('Session Key', max_length=100, null=True, blank=True)
    clicked_at = models.DateTimeField('Clicked At', auto_now_add=True)
    success = models.BooleanField('Success?', default=True)
    
    class Meta:
        verbose_name = 'WhatsApp Click'
        verbose_name_plural = 'WhatsApp Clicks'
        ordering = ['-clicked_at']
    
    def __str__(self):
        return f"Click on {self.advertisement.title} at {self.clicked_at}"


class PaymentPlan(models.Model):
    name = models.CharField('Plan Name', max_length=100)
    description = models.TextField('Description', blank=True)
    highlight_type = models.CharField(
        'Highlight Type',
        max_length=20,
        choices=Advertisement.HIGHLIGHT_CHOICES
    )
    duration_days = models.PositiveIntegerField('Duration (days)')
    price = models.DecimalField('Price', max_digits=10, decimal_places=2)
    is_active = models.BooleanField('Is Active?', default=True)
    features = models.JSONField('Features', default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Payment Plan'
        verbose_name_plural = 'Payment Plans'
        ordering = ['price']
    
    def __str__(self):
        return f"{self.name} - {self.price} STN"


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Card'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='User'
    )
    advertisement = models.ForeignKey(
        Advertisement,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments',
        verbose_name='Advertisement'
    )
    plan = models.ForeignKey(
        PaymentPlan,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Plan'
    )
    
    amount = models.DecimalField('Amount', max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        'Payment Method',
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    transaction_id = models.CharField(
        'Transaction ID',
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )
    payment_data = models.JSONField('Payment Data', default=dict, blank=True)
    
    paid_at = models.DateTimeField('Paid At', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment from {self.user.name} - {self.amount} STN"
    
    def mark_as_paid(self):
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.save()
        
        if self.advertisement and self.plan:
            self.advertisement.highlight_type = self.plan.highlight_type
            
            if self.advertisement.expiration_date:
                new_expiration = max(
                    self.advertisement.expiration_date,
                    timezone.now()
                ) + timezone.timedelta(days=self.plan.duration_days)
                self.advertisement.expiration_date = new_expiration
            else:
                self.advertisement.expiration_date = timezone.now() + timezone.timedelta(days=self.plan.duration_days)
            
            if self.advertisement.status != 'active':
                self.advertisement.status = 'active'
                self.advertisement.published_at = timezone.now()
            
            self.advertisement.save()