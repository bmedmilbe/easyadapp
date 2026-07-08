# ads/admin.py
from django.contrib import admin

from .models import (
    Advertisement,
    AdvertisementClick,
    AdvertisementImage,
    AdvertisementView,
    Category,
    Payment,
    PaymentPlan,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'is_active', 'order']
    search_fields = ['name', 'slug']
    list_filter = ['is_active', 'parent']
    prepopulated_fields = {'slug': ('name',)}


class AdvertisementImageInline(admin.TabularInline):
    model = AdvertisementImage
    extra = 3
    fields = ['image', 'caption', 'order', 'is_primary']


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'status', 'highlight_type', 'price', 'is_active']
    list_filter = ['status', 'highlight_type', 'category', 'is_anonymous', 'created_at']
    search_fields = ['title', 'description', 'user__name', 'user__phone_number']
    readonly_fields = ['views_count', 'whatsapp_clicks', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Ad Information', {
            'fields': ('user', 'category', 'title', 'description', 'price', 'is_price_negotiable')
        }),
        ('Status & Visibility', {
            'fields': ('status', 'highlight_type', 'published_at', 'expiration_date')
        }),
        ('EasyFlow', {
            'fields': ('session_key', 'is_anonymous', 'temp_user_data'),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('views_count', 'whatsapp_clicks', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [AdvertisementImageInline]
    
    actions = ['activate_ads', 'suspend_ads']
    
    def activate_ads(self, request, queryset):
        queryset.update(status='active')
    activate_ads.short_description = "Activate selected ads"
    
    def suspend_ads(self, request, queryset):
        queryset.update(status='suspended')
    suspend_ads.short_description = "Suspend selected ads"


@admin.register(AdvertisementImage)
class AdvertisementImageAdmin(admin.ModelAdmin):
    list_display = ['advertisement', 'order', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['advertisement__title', 'caption']


@admin.register(AdvertisementView)
class AdvertisementViewAdmin(admin.ModelAdmin):
    list_display = ['advertisement', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at']
    readonly_fields = ['viewed_at']


@admin.register(AdvertisementClick)
class AdvertisementClickAdmin(admin.ModelAdmin):
    list_display = ['advertisement', 'success', 'clicked_at']
    list_filter = ['success', 'clicked_at']
    readonly_fields = ['clicked_at']


@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'highlight_type', 'duration_days', 'price', 'is_active']
    list_filter = ['highlight_type', 'is_active']
    search_fields = ['name']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'payment_method', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['user__name', 'user__phone_number', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['mark_as_paid']
    
    def mark_as_paid(self, request, queryset):
        for payment in queryset:
            payment.mark_as_paid()
    mark_as_paid.short_description = "Mark selected payments as paid"