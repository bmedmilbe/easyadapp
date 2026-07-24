# core/views.py

from ads.models import TemporaryAd
from django.db import transaction
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    ChangePinSerializer,
    ResendPinSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
)
from .utils import send_pin_sms

# core/views.py

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                user = serializer.save()
                pin = user._generated_pin

            # Reuse helper here!
            sms_sent = send_pin_sms(user.mobile_number, pin)
            
            return Response({
                'message': 'User registered successfully.' if sms_sent else 'User registered, but failed to send SMS.',
                'mobile_number': user.mobile_number,
                'district': user.district,
                'pin_sent': sms_sent
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': f'Registration failed: {e!s}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResendPinView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResendPinSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user, new_pin = serializer.save()
            
            # Reuse helper here!
            sms_sent = send_pin_sms(user.mobile_number, new_pin)
            
            return Response({
                'message': 'New PIN sent via SMS.',
                'mobile_number': user.mobile_number,
                'pin_sent': sms_sent
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': f'Failed to resend PIN: {e!s}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class LoginView(APIView):
    """
    API view for user login with mobile number and PIN.
    """
    permission_classes = [AllowAny]
    
    @transaction.atomic
    def post(self, request):
        """
        Authenticate user and return token.
        """
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.validated_data['user']
        
        # Get or create authentication token
        token, _ = Token.objects.get_or_create(user=user)
        
        # Check if there's a pending temporary ad to transfer
        pending_token = request.data.get('pending_ad_token')
        transferred_ad = None
        
        if pending_token:
            try:
                temp_ad = TemporaryAd.objects.get(session_token=pending_token)
                if hasattr(user, 'profile'):
                    transferred_ad = temp_ad.transfer_to_official_ad(user.profile)
            except TemporaryAd.DoesNotExist:
                # Invalid token, but we still log the user in
                pass
        
        return Response({
            'token': token.key,
            'user_id': user.id,
            'mobile_number': user.mobile_number,
            'district': user.district,
            'transferred_ad_id': transferred_ad.id if transferred_ad else None
        }, status=status.HTTP_200_OK)


class ChangePinView(UpdateAPIView):
    """
    API view for authenticated users to change their PIN.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePinSerializer
    
    def get_object(self):
        """
        Return the current user.
        """
        return self.request.user
    
    def get_serializer_context(self):
        """
        Add user to serializer context.
        """
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context
    
    def update(self, request, *args, **kwargs):
        """
        Update user's PIN.
        """
        user = self.get_object()
        serializer = self.get_serializer(data=request.data, context={'user': user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'PIN changed successfully.',
            'mobile_number': user.mobile_number
        }, status=status.HTTP_200_OK)