# ads/admin.py
from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import (
    Ad,
    AdImage,
    AdStatus,
    Category,
    CustomerProfile,
    TemporaryAd,
    TemporaryAdImage,
)


class AdImageInline(admin.TabularInline):
    """
    Inline for AdImage within AdAdmin.
    Allows admins to view and manage images directly on the ad page.
    """
    model = AdImage
    extra = 1  # Show one empty form
    fields = ('image', 'caption', 'order', 'image_preview')
    readonly_fields = ('image_preview',)
    ordering = ('order', 'created_at')
    
    def image_preview(self, obj):
        """
        Display a thumbnail preview of the image in the admin.
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


class AdAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Ad model.
    """
    inlines = [AdImageInline]
    
    # Display fields in the list view
    list_display = (
        'product_name',
        'customer_display',
        'category',
        'status',
        'is_featured',
        'created_at',
        'expires_at',
        'image_count',
        'is_expired_display'
    )
    
    # Editable fields directly in the list view
    list_editable = ['status', 'is_featured']
    
    # Fields for filtering in the sidebar
    list_filter = (
        'status',
        'is_featured',
        'category',
        'created_at',
    )
    
    # Search fields
    search_fields = (
        'product_name',
        'description',
        'customer__user__mobile_number',
    )
    
    # Ordering
    ordering = ('-is_featured', '-created_at')
    
    # Fieldsets for the detail/edit view
    fieldsets = (
        (None, {
            'fields': (
                'customer',
                'category',
                'product_name',
                'description',
                'price'
            )
        }),
        ('Status & Scheduling', {
            'fields': (
                'status',
                'is_featured',
                'expires_at'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'System timestamps - read only'
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    # Date hierarchy for better navigation
    date_hierarchy = 'created_at'
    
    # Performance optimization
    list_select_related = ('customer', 'customer__user', 'category')
    
    def customer_display(self, obj):
        """
        Display customer information in list view.
        """
        return obj.customer.user.mobile_number
    customer_display.short_description = 'Vendor'
    customer_display.admin_order_field = 'customer__user__mobile_number'
    
    def image_count(self, obj):
        """
        Display the number of images attached to the ad.
        """
        count = obj.images.count()
        return format_html(
            '<span style="background-color: #f0f0f0; padding: 2px 8px; border-radius: 12px;">{}</span>',
            count
        )
    image_count.short_description = 'Images'
    
    def is_expired_display(self, obj):
        """
        Display whether the ad is expired.
        """
        if obj.is_expired():
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">✓ Expired</span>'
            )
        return format_html(
            '<span style="color: #28a745;">Active</span>'
        )
    is_expired_display.short_description = 'Expired?'
    
    def get_queryset(self, request):
        """
        Optimize queryset with annotations for better performance.
        """
        return super().get_queryset(request).annotate(
            image_count_annotated=Count('images')
        )
    
    def save_model(self, request, obj, form, change):
        """
        Override save to handle expiration status automatically.
        """
        if obj.is_expired() and obj.status != AdStatus.EXPIRED:
            obj.status = AdStatus.EXPIRED
        super().save_model(request, obj, form, change)
    
    actions = ['make_active', 'make_suspended', 'make_expired', 'make_featured']
    
    def make_active(self, request, queryset):
        """
        Admin action to set selected ads as active.
        """
        updated = queryset.update(status=AdStatus.ACTIVE)
        self.message_user(request, f'{updated} ad(s) marked as active.')
    make_active.short_description = 'Mark selected ads as Active'
    
    def make_suspended(self, request, queryset):
        """
        Admin action to suspend selected ads.
        """
        updated = queryset.update(status=AdStatus.SUSPENDED)
        self.message_user(request, f'{updated} ad(s) suspended.')
    make_suspended.short_description = 'Suspend selected ads'
    
    def make_expired(self, request, queryset):
        """
        Admin action to mark selected ads as expired.
        """
        updated = queryset.update(status=AdStatus.EXPIRED)
        self.message_user(request, f'{updated} ad(s) marked as expired.')
    make_expired.short_description = 'Mark selected ads as Expired'
    
    def make_featured(self, request, queryset):
        """
        Admin action to feature selected ads.
        """
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} ad(s) marked as featured.')
    make_featured.short_description = 'Feature selected ads'


class TemporaryAdImageInline(admin.TabularInline):
    """
    Inline for TemporaryAdImage within TemporaryAdAdmin.
    """
    model = TemporaryAdImage
    extra = 1
    fields = ('image', 'caption', 'order', 'image_preview')
    readonly_fields = ('image_preview',)
    ordering = ('order', 'created_at')
    
    def image_preview(self, obj):
        """
        Display a thumbnail preview of the temporary image.
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


class TemporaryAdAdmin(admin.ModelAdmin):
    """
    Admin configuration for the TemporaryAd model.
    Allows admins to monitor abandoned drafts.
    """
    inlines = [TemporaryAdImageInline]
    
    list_display = (
        'product_name',
        'category',
        'session_token_short',
        'created_at',
        'updated_at',
        'has_images',
        'age_display'
    )
    
    list_filter = (
        'category',
        'created_at',
    )
    
    search_fields = (
        'product_name',
        'description',
        'session_token',
    )
    
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': (
                'product_name',
                'description',
                'price',
                'category'
            )
        }),
        ('Session Information', {
            'fields': ('session_token', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('session_token', 'created_at', 'updated_at')
    
    date_hierarchy = 'created_at'
    
    def session_token_short(self, obj):
        """
        Display a shortened version of the session token.
        """
        return str(obj.session_token)[:8] + '...'
    session_token_short.short_description = 'Session Token'
    
    def has_images(self, obj):
        """
        Display whether the temporary ad has images.
        """
        count = obj.temporary_images.count()
        return count > 0
    has_images.boolean = True
    has_images.short_description = 'Has Images'
    
    def age_display(self, obj):
        """
        Display the age of the temporary ad.
        """
        from django.utils import timezone
        age = timezone.now() - obj.created_at
        days = age.days
        hours = age.seconds // 3600
        
        if days > 0:
            return f'{days} day(s)'
        elif hours > 0:
            return f'{hours} hour(s)'
        else:
            return '< 1 hour'
    age_display.short_description = 'Age'
    
    actions = ['delete_old_drafts']
    
    def delete_old_drafts(self, request, queryset):
        """
        Admin action to delete old temporary ads.
        """
        from datetime import timedelta

        from django.utils import timezone
        
        old_drafts = queryset.filter(
            created_at__lt=timezone.now() - timedelta(days=7)
        )
        count = old_drafts.count()
        old_drafts.delete()
        self.message_user(request, f'{count} old draft(s) deleted.')
    delete_old_drafts.short_description = 'Delete drafts older than 7 days'


class CategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Category model.
    """
    prepopulated_fields = {'slug': ('name',)}
    
    list_display = (
        'name',
        'slug',
        'description_short',
        'ad_count',
        'created_at'
    )
    
    search_fields = ('name', 'description')
    
    ordering = ('name',)
    
    def description_short(self, obj):
        """
        Show truncated description.
        """
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    
    def ad_count(self, obj):
        """
        Display number of ads in this category.
        """
        return obj.ads.count()
    ad_count.short_description = 'Ads'


# Register the models with their custom admin classes
admin.site.register(Category, CategoryAdmin)
admin.site.register(Ad, AdAdmin)
admin.site.register(TemporaryAd, TemporaryAdAdmin)

# Register CustomerProfile separately if needed (optional)
@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    """
    Separate admin for CustomerProfile if needed.
    """
    list_display = ('user_mobile', 'user_district', 'created_at', 'updated_at')
    search_fields = ('user__mobile_number',)
    list_filter = ('user__district',)
    readonly_fields = ('created_at', 'updated_at')
    
    def user_mobile(self, obj):
        return obj.user.mobile_number
    user_mobile.short_description = 'Mobile Number'
    
    def user_district(self, obj):
        return obj.user.district
    user_district.short_description = 'District'