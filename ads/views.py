
from django.db import transaction
from rest_framework import generics, status, viewsets
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .models import Ad, AdImage, Category, TemporaryAd, TemporaryAdImage
from .serializers import (
    AdImageSerializer,
    AdSerializer,
    CategorySerializer,
    TemporaryAdImageSerializer,
    TemporaryAdSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for categories.
    Publicly accessible.
    """
    permission_classes = [AllowAny]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'


class AdViewSet(viewsets.ModelViewSet):
    """
    ViewSet for production advertisements.
    - Public: list and retrieve
    - Authenticated: create, update, destroy
    """
    queryset = Ad.objects.all()
    serializer_class = AdSerializer
    
    def get_permissions(self):
        """
        Custom permission handling:
        - list and retrieve: AllowAny
        - create, update, destroy: IsAuthenticated
        """
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    def get_queryset(self):
        """
        Optionally filter queryset by query parameters.
        """
        queryset = super().get_queryset()
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Filter by featured status
        featured = self.request.query_params.get('featured')
        if featured and featured.lower() == 'true':
            queryset = queryset.filter(is_featured=True)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Automatically inject the authenticated user's profile.
        """
        if not hasattr(self.request.user, 'profile'):
            raise ValueError("User does not have a customer profile.")
        
        serializer.save(customer=self.request.user.profile)
    
    def perform_update(self, serializer):
        """
        Update ad with ownership check.
        """
        ad = self.get_object()
        
        # Ensure the user owns the ad
        if ad.customer.user != self.request.user:
            raise PermissionError("You do not have permission to edit this ad.")
        
        # Prevent modification of is_featured flag by regular users
        if 'is_featured' in serializer.validated_data:
            del serializer.validated_data['is_featured']
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """
        Delete ad with ownership check.
        """
        if instance.customer.user != self.request.user:
            raise PermissionError("You do not have permission to delete this ad.")
        
        instance.delete()


class GuestAdCreateView(generics.GenericAPIView):
    """
    Public view for anonymous users to create temporary ads.
    """
    permission_classes = [AllowAny]
    serializer_class = TemporaryAdSerializer
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        Create a temporary ad with images for guest users.
        """
        # Extract and validate main ad data
        ad_data = {
            'product_name': request.data.get('product_name'),
            'description': request.data.get('description', ''),
            'price': request.data.get('price')
        }
        
        # Handle category if provided
        category_id = request.data.get('category')
        if category_id:
            try:
                from .models import Category
                category = Category.objects.get(id=category_id)
                ad_data['category'] = category.id
            except (Category.DoesNotExist, ValueError):
                return Response({
                    'error': 'Invalid category ID.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate with serializer
        serializer = self.get_serializer(data=ad_data)
        serializer.is_valid(raise_exception=True)
        
        # Create temporary ad
        temp_ad = serializer.save()
        
        # Handle image uploads
        images = request.FILES.getlist('images')
        if images:
            for image in images:
                TemporaryAdImage.objects.create(
                    temporary_ad=temp_ad,
                    image=image
                )
        
        # Return response with session token
        return Response({
            'message': 'Temporary ad created successfully.',
            'session_token': str(temp_ad.session_token),
            'ad': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def put(self, request, *args, **kwargs):
        """
        Update an existing temporary ad by session token.
        """
        session_token = request.data.get('session_token')
        if not session_token:
            return Response({
                'error': 'session_token is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find the temporary ad
        try:
            temp_ad = TemporaryAd.objects.get(session_token=session_token)
        except TemporaryAd.DoesNotExist:
            return Response({
                'error': 'Invalid or expired session token.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Update main fields
        temp_ad.product_name = request.data.get('product_name', temp_ad.product_name)
        temp_ad.description = request.data.get('description', temp_ad.description)
        temp_ad.price = request.data.get('price', temp_ad.price)
        
        # Update category if provided
        category_id = request.data.get('category')
        if category_id:
            try:
                from .models import Category
                temp_ad.category = Category.objects.get(id=category_id)
            except (Category.DoesNotExist, ValueError):
                pass
        
        temp_ad.save()
        
        # Handle new images (append to existing ones)
        images = request.FILES.getlist('images')
        if images:
            for image in images:
                TemporaryAdImage.objects.create(
                    temporary_ad=temp_ad,
                    image=image
                )
        
        # Return updated ad
        serializer = self.get_serializer(temp_ad)
        return Response({
            'message': 'Temporary ad updated successfully.',
            'ad': serializer.data
        }, status=status.HTTP_200_OK)
    
    def delete(self, request, *args, **kwargs):
        """
        Delete a temporary ad by session token.
        """
        session_token = request.data.get('session_token')
        if not session_token:
            return Response({
                'error': 'session_token is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            temp_ad = TemporaryAd.objects.get(session_token=session_token)
            temp_ad.delete()
            return Response({
                'message': 'Temporary ad deleted successfully.'
            }, status=status.HTTP_200_OK)
        except TemporaryAd.DoesNotExist:
            return Response({
                'error': 'Invalid or expired session token.'
            }, status=status.HTTP_404_NOT_FOUND)
        



class AdImageViewSet(viewsets.ModelViewSet):
    '''
    ViewSet for managing images on official ads.
    - List and retrieve: Public (but filtered by ad)
    - Create, update, delete: Authenticated users who own the ad
    '''
    serializer_class = AdImageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        '''
        Filter images by the parent ad.
        '''
        ad_id = self.kwargs.get('ad_pk')
        return AdImage.objects.filter(ad_id=ad_id)
    
    def perform_create(self, serializer):
        '''
        Create an image for the specified ad.
        Ensure the user owns the ad.
        '''
        ad_id = self.kwargs.get('ad_pk')
        from .models import Ad
        
        try:
            ad = Ad.objects.get(id=ad_id)
            # Check ownership
            if ad.customer.user != self.request.user:
                raise PermissionError("You do not own this ad.")
            
            serializer.save(ad=ad)
        except Ad.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Ad not found.")
    
    def perform_update(self, serializer):
        '''
        Update an image with ownership check.
        '''
        image = self.get_object()
        if image.ad.customer.user != self.request.user:
            raise PermissionError("You do not own this ad.")
        serializer.save()
    
    def perform_destroy(self, instance):
        '''
        Delete an image with ownership check.
        '''
        if instance.ad.customer.user != self.request.user:
            raise PermissionError("You do not own this ad.")
        instance.delete()


class TemporaryAdViewSet(viewsets.ModelViewSet):
    '''
    ViewSet for temporary ads (guest flow).
    Uses session token for identification instead of authentication.
    '''
    serializer_class = TemporaryAdSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        '''
        Filter temporary ads by session token from the request.
        '''
        session_token = self.request.query_params.get('session_token')
        if session_token:
            return TemporaryAd.objects.filter(session_token=session_token)
        return TemporaryAd.objects.none()
    
    def create(self, request, *args, **kwargs):
        '''
        Override create to handle the session token generation.
        '''
        # Existing logic from GuestAdCreateView but adapted for ViewSet
        return super().create(request, *args, **kwargs)


class TemporaryAdImageViewSet(viewsets.ModelViewSet):
    '''
    ViewSet for managing images on temporary ads.
    No authentication required, uses session token for identification.
    '''
    serializer_class = TemporaryAdImageSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        '''
        Filter temporary images by the parent temporary ad.
        '''
        temp_ad_id = self.kwargs.get('temporary_ad_pk')
        return TemporaryAdImage.objects.filter(temporary_ad_id=temp_ad_id)
    
    def perform_create(self, serializer):
        '''
        Create an image for the specified temporary ad.
        '''
        temp_ad_id = self.kwargs.get('temporary_ad_pk')
        from .models import TemporaryAd
        
        try:
            temp_ad = TemporaryAd.objects.get(id=temp_ad_id)
            # Optional: Verify session token if needed
            session_token = self.request.query_params.get('session_token')
            if session_token and temp_ad.session_token != session_token:
                raise PermissionError("Invalid session token.")
            
            serializer.save(temporary_ad=temp_ad)
        except TemporaryAd.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Temporary ad not found.")
    
    def perform_update(self, serializer):
        '''
        Update an image with session token check.
        '''
        image = self.get_object()
        session_token = self.request.query_params.get('session_token')
        if session_token and image.temporary_ad.session_token != session_token:
            raise PermissionError("Invalid session token.")
        serializer.save()
    
    def perform_destroy(self, instance):
        '''
        Delete an image with session token check.
        '''
        session_token = self.request.query_params.get('session_token')
        if session_token and instance.temporary_ad.session_token != session_token:
            raise PermissionError("Invalid session token.")
        instance.delete()
