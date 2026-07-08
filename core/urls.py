# core/urls.py
from django.urls import path

from .views import ChangePinView, LoginView, RegisterView

app_name = 'core'



urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', LoginView.as_view(), name='auth_login'),
    path('change-pin/', ChangePinView.as_view(), name='auth_change_pin'),
]