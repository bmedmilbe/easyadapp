# core/views.py
import random

from ads.models import TemporaryAd
from django.db import transaction
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import CustomUser
from .serializers import (
    ChangePinSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
)


class RegisterView(generics.GenericAPIView):
    """
    Registration view that generates a 4-digit PIN and creates a user.
    """
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    
    def generate_pin(self):
        """Generate a random 4-digit PIN."""
        return ''.join(random.choices('0123456789', k=4))
    
    def send_pin_via_sms(self, mobile_number, pin):
        """
        Mock SMS sending functionality.
        In production, integrate with an actual SMS gateway.
        """
        print(f"[SMS MOCK] Sending PIN {pin} to {mobile_number}")
        # Placeholder for actual SMS gateway integration
        return True
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        Register a new user with a generated PIN.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Generate random 4-digit PIN
        pin = self.generate_pin()
        
        # Create user with the generated PIN
        user = CustomUser.objects.create_user(
            mobile_number=serializer.validated_data['mobile_number'],
            district=serializer.validated_data['district'],
            pin=pin
        )
        
        # # Create associated CustomerProfile
        # CustomerProfile.objects.create(user=user)
        
        # Send PIN via SMS (mock)
        self.send_pin_via_sms(user.mobile_number, pin)
        
        return Response({
            'message': 'User registered successfully. PIN sent via SMS.',
            'mobile_number': user.mobile_number,
            'district': user.district
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """
    Login view that authenticates using mobile number and PIN.
    Supports transferring temporary ads to the user's profile.
    """
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        Authenticate user and handle pending temporary ad transfer.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Get or create authentication token
        token, _ = Token.objects.get_or_create(user=user)
        
        # Handle pending temporary ad transfer
        pending_token = request.data.get('pending_ad_token')
        transferred_ad_id = None
        
        if pending_token:
            try:
                # Look up the temporary ad by session token
                temp_ad = TemporaryAd.objects.get(session_token=pending_token)
                
                # Transfer to official ad using the user's profile
                if hasattr(user, 'profile'):
                    official_ad = temp_ad.transfer_to_official_ad(user.profile)
                    transferred_ad_id = official_ad.id
            except TemporaryAd.DoesNotExist:
                # Invalid token, continue without transfer
                pass
        
        return Response({
            'token': token.key,
            'user_id': user.id,
            'mobile_number': user.mobile_number,
            'district': user.district,
            'transferred_ad_id': transferred_ad_id
        }, status=status.HTTP_200_OK)


class ChangePinView(generics.UpdateAPIView):
    """
    View for authenticated users to change their PIN.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePinSerializer
    
    def get_object(self):
        """Return the current authenticated user."""
        return self.request.user
    
    def get_serializer_context(self):
        """Add user to serializer context."""
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context
    
    def update(self, request, *args, **kwargs):
        """
        Update user's PIN and return success response.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': 'PIN changed successfully.',
            'mobile_number': instance.mobile_number
        }, status=status.HTTP_200_OK)