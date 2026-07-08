# ads/views.py
from core.models import SessionManager
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Advertisement, Category
from .serializers import (
    AdvertisementCreateSerializer,
    AdvertisementSerializer,
    CategorySerializer,
)


class AdvertisementViewSet(viewsets.ModelViewSet):
    queryset = Advertisement.objects.filter(status='active')
    serializer_class = AdvertisementSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AdvertisementCreateSerializer
        return AdvertisementSerializer
    
    def create(self, request, *args, **kwargs):
        # EasyFlow: Get or create session
        session_key = request.COOKIES.get('easyflow_session')
        
        # Check if user is authenticated
        if request.user.is_authenticated:
            user = request.user
            is_anonymous = False
        else:
            # Create anonymous ad
            user = None
            is_anonymous = True
            
            # Store temp data in session
            if session_key:
                session, _ = SessionManager.objects.get_or_create(
                    session_key=session_key,
                    defaults={
                        'expires_at': timezone.now() + timezone.timedelta(days=30)
                    }
                )
                session.data = request.data.get('temp_user_data', {})
                session.save()
        
        # Create advertisement
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ad = serializer.save(
            user=request.user if request.user.is_authenticated else None,
            is_anonymous=is_anonymous,
            session_key=session_key if not request.user.is_authenticated else None,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response(
            AdvertisementSerializer(ad).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def claim(self, request, pk=None):
        """Claim an anonymous ad after authentication"""
        ad = get_object_or_404(Advertisement, pk=pk, is_anonymous=True)
        
        if request.user.is_authenticated:
            ad.assign_to_user(request.user)
            return Response({'status': 'ad claimed successfully'})
        return Response(
            {'error': 'user must be authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    @action(detail=True, methods=['get'])
    def whatsapp(self, request, pk=None):
        """Get WhatsApp link and track click"""
        ad = get_object_or_404(Advertisement, pk=pk, status='active')
        ad.increment_whatsapp_clicks()
        
        # Record click
        from .models import AdvertisementClick
        AdvertisementClick.objects.create(
            advertisement=ad,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            session_key=request.COOKIES.get('easyflow_session'),
            success=True
        )
        
        return Response({
            'whatsapp_link': ad.get_whatsapp_link(),
            'message': f"Hi, I'm interested in your {ad.title}"
        })
    
    @action(detail=False, methods=['get'])
    def highlights(self, request):
        """Get highlighted ads"""
        highlighted = self.get_queryset().filter(
            highlight_type__in=['basic', 'premium', 'featured']
        ).order_by('-highlight_type', '-published_at')[:20]
        
        serializer = self.get_serializer(highlighted, many=True)
        return Response(serializer.data)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]