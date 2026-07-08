# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    District,
    SessionManager,
    SiteConfiguration,
    SystemLog,
    User,
    UserProfile,
)


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_diaspora']
    search_fields = ['name', 'code']
    list_filter = ['is_diaspora']


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['phone_number', 'name', 'district', 'is_verified', 'is_active']
    search_fields = ['phone_number', 'name']
    list_filter = ['is_verified', 'is_active', 'district']
    
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal Info', {'fields': ('name', 'district')}),
        ('PIN', {'fields': ('pin_code', 'pin_created_at', 'is_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'name', 'district', 'password1', 'password2'),
        }),
    )
    
    ordering = ['-date_joined']
    inlines = [UserProfileInline]


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ['type', 'user', 'message', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['message', 'user__name', 'user__phone_number']
    readonly_fields = ['created_at']


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        if SiteConfiguration.objects.exists():
            return False
        return True


@admin.register(SessionManager)
class SessionManagerAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'user', 'expires_at', 'created_at']
    list_filter = ['created_at', 'expires_at']
    search_fields = ['session_key', 'user__name', 'user__phone_number']