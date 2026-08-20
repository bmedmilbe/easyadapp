
# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# from .models import User


# class CustomUserAdmin(BaseUserAdmin):
#     """
#     Custom admin configuration for the CustomUser model.
#     """
    
#     # Display fields in the list view
#     list_display = (
#         'mobile_number', 
#         'fisrt_name', 
#         'last_name', 
#     )
    
#     # Fields for filtering in the sidebar
#     list_filter = (
#         'is_active',
#         'is_staff',
#         'is_superuser',
#     )
    
#     # Search fields
#     search_fields = ('mobile_number','first_name', 'last_name')
    
#     # Ordering
#     ordering = ('-date_joined','first_name')
    
   
    
    
#     readonly_fields = ('date_joined',)
    
#     def get_queryset(self, request):
#         """
#         Optimize queryset with select_related for better performance.
#         """
#         return super().get_queryset(request).select_related('profile')


# # Register the custom user model with the custom admin
# admin.site.register(User, CustomUserAdmin)