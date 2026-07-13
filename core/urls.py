# core/urls.py
from django.urls import path

from .views import ChangePinView, LoginView, RegisterView, ResendPinView

app_name = 'core'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', LoginView.as_view(), name='auth_login'),
    path('change-pin/', ChangePinView.as_view(), name='auth_change_pin'),
    path('resend-pin/', ResendPinView.as_view(), name='auth_resend_pin'),
]