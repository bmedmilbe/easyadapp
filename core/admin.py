
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


class CustomUserAdmin(BaseUserAdmin):
    """
    Custom admin configuration for the CustomUser model.
    """
    
    # Display fields in the list view
    list_display = (
        'mobile_number', 
        'district', 
        'is_active', 
        'is_staff', 
        'is_superuser',
        'date_joined'
    )
    
    # Fields for filtering in the sidebar
    list_filter = (
        'district',
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined'
    )
    
    # Search fields
    search_fields = ('mobile_number',)
    
    # Ordering
    ordering = ('-date_joined',)
    
    # Fieldsets for the detail/edit view
    fieldsets = (
        (None, {
            'fields': ('mobile_number', 'district', 'password')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 
                'is_staff', 
                'is_superuser',
                'groups',
                'user_permissions'
            ),
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    # Fieldsets for adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('mobile_number', 'district', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined',)
    
    def get_queryset(self, request):
        """
        Optimize queryset with select_related for better performance.
        """
        return super().get_queryset(request).select_related('profile')


# Register the custom user model with the custom admin
admin.site.register(CustomUser, CustomUserAdmin)