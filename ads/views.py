import hashlib
from functools import wraps

from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, permissions, viewsets
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .models import (
    Ad,
    AdImage,
    Category,
    CustomerProfile,
    TemporaryAd,
    TemporaryAdImage,
)
from .serializers import (
    AdCreateSerializer,
    AdImageSerializer,
    AdSerializer,
    CategorySerializer,
    TemporaryAdImageSerializer,
    TemporaryAdSerializer,
)


def custom_cache_version(cache_name_pattern, timeout=60 * 60):
    """
    A reusable decorator for DRF ViewSet methods (list, retrieve).
    Supports dynamic string formatting using view kwargs (e.g., 'ads_{pk}').
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):

            # 1. Resolve dynamic cache names like "ads_{pk}" using url kwargs
            # If kwargs contains {'pk': 5}, "ads_{pk}" becomes "ads_5"
            try:
                cache_name = cache_name_pattern.format(**kwargs)
            except KeyError:
                cache_name = cache_name_pattern

            # 2. Fetch the specific version tracker from Redis
            cache_version = cache.get_or_set(f"{cache_name}_cache_version", 1)

            # 3. Handle query parameters (useful if retrieve has variations like ?expand=true)
            query_params = request.query_params.dict()
            if query_params:
                sorted_params = sorted(query_params.items())
                params_string = "&".join(f"{k}={v}" for k, v in sorted_params)
                params_hash = hashlib.md5(params_string.encode("utf-8")).hexdigest()
                cache_key = f"api_{cache_name}_{params_hash}"
            else:
                cache_key = f"api_{cache_name}_clean"

            # 4. Check Redis cache hit
            cached_data = cache.get(cache_key, version=cache_version)
            if cached_data:
                return Response(cached_data)
            # 5. Cache Miss: Execute original method
            response = func(self, request, *args, **kwargs)

            # 6. Store response data
            cache.set(cache_key, response.data, timeout=timeout, version=cache_version)

            return response

        return wrapper

    return decorator


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for categories.
    Publicly accessible.
    """

    permission_classes = [AllowAny]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    lookup_field = "slug"

    @custom_cache_version("categories", 60 * 60 * 24)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class AdViewViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Publicly accessible Read-Only ViewSet for listing and retrieving ads.
    """

    queryset = Ad.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [
        filters.SearchFilter,
        DjangoFilterBackend,
        filters.OrderingFilter,
    ]

    filterset_fields = {
        "status": ["exact"],
        "is_featured": ["exact"],
        "price": ["exact", "gt", "lte"],
        "condition": ["exact"],
    }
    serializer_class = AdSerializer

    @custom_cache_version("ads", 60 * 60)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @custom_cache_version("ads_{pk}", timeout=60 * 60)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class AdManageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for authenticated users to manage (list,add, edit, delete) their own ads.
    """

    queryset = Ad.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    # Restrict to only add, edit, and delete actions
    http_method_names = ["post", "get", "put", "patch", "delete"]

    filter_backends = [
        filters.SearchFilter,
        DjangoFilterBackend,
        filters.OrderingFilter,
    ]

    search_fields = [
        "product_name",
        "description",
        "category__name",
        "category__description",
    ]

    filterset_fields = {
        "status": ["exact"],
        "is_featured": ["exact"],
        "price": ["exact", "gt", "lte"],
        "condition": ["exact"],
    }

    def get_queryset(self):
        """
        Ensures users can only view or mutate their own products.
        """
        user = self.request.user
        if not user or user.is_anonymous:
            return Ad.objects.none()

        try:
            customer = CustomerProfile.objects.get(user=user)
            return Ad.objects.filter(customer_id=customer.id)
        except CustomerProfile.DoesNotExist:
            return Ad.objects.none()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AdCreateSerializer
        return AdSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()

        if self.request.user.is_authenticated:
            try:
                customer = CustomerProfile.objects.get(user=self.request.user)
                context["customer_id"] = customer.id
            except CustomerProfile.DoesNotExist:
                context["customer_id"] = None

        context["temp_ad_id"] = self.kwargs.get("temporary_ad_pk")
        return context

    def list(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            customer = CustomerProfile.objects.get(user=self.request.user)
            customer_id = customer.id

            # Dynamically instantiate the decorator inside the function execution block
            @custom_cache_version(f"ads_manage_customer_{customer_id}", timeout=60 * 60)
            def get_cached_list(inner_self, inner_request, *inner_args, **inner_kwargs):
                return super(AdManageViewSet, self).list(request, *args, **kwargs)

            # Execute the safely wrapped method passing down instances
            return get_cached_list(self, request, *args, **kwargs)

        # Fallback response if the user somehow reaches here unauthenticated
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )

    def retrieve(self, request, *args, **kwargs):
        # Fetch the target instance to capture its unique ID
        obj = self.get_object()

        # Dynamically instantiate the decorator matching your unique instance ID pattern
        @custom_cache_version(f"ads_manage_{obj.id}", timeout=60 * 60)
        def get_cached_retrieve(inner_self, inner_request, *inner_args, **inner_kwargs):
            return super(AdManageViewSet, self).retrieve(request, *args, **kwargs)

        return get_cached_retrieve(self, request, *args, **kwargs)


class AdImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing images on official ads.
    """

    serializer_class = AdImageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        Filter images by the parent ad.
        """
        ad_id = self.kwargs.get("ad_pk")
        return AdImage.objects.filter(ad_id=ad_id)

    def list(self, request, *args, **kwargs):
        # Extract the ad ID directly from the URL kwargs (e.g., from nested routing)
        ad_id = self.kwargs.get("ad_pk")

        # Instantiate the decorator inline to capture the dynamic ad_id
        @custom_cache_version(f"ads_images_{ad_id}", timeout=60 * 60)
        def get_cached_images_list(
            inner_self, inner_request, *inner_args, **inner_kwargs
        ):
            return super(AdImageViewSet, self).list(request, *args, **kwargs)

        return get_cached_images_list(self, request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        # Fetch the specific AdImage instance to capture its unique ID
        obj = self.get_object()

        # Instantiate the decorator inline matching your image-specific cache key
        @custom_cache_version(f"ads_image_{obj.id}", timeout=60 * 60)
        def get_cached_image_detail(
            inner_self, inner_request, *inner_args, **inner_kwargs
        ):
            return super(AdImageViewSet, self).retrieve(request, *args, **kwargs)

        return get_cached_image_detail(self, request, *args, **kwargs)


class TemporaryAdViewSet(
    mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    ViewSet for temporary ads (guest flow).
    Allows ONLY creation (POST) and retrieval (GET detail).
    """

    serializer_class = TemporaryAdSerializer
    permission_classes = [AllowAny]
    queryset = TemporaryAd.objects.all()

    def retrieve(self, request, *args, **kwargs):
        # Fetch the specific TemporaryAd instance to capture its unique ID
        obj = self.get_object()

        # Instantiate the decorator inline matching your temporary ad-specific cache key
        @custom_cache_version(
            f"temp_ad_{obj.id}", timeout=60 * 600
        )  # 10-minute timeout for temporary objects
        def get_cached_temp_ad_detail(
            inner_self, inner_request, *inner_args, **inner_kwargs
        ):
            return super(TemporaryAdViewSet, self).retrieve(request, *args, **kwargs)

        return get_cached_temp_ad_detail(self, request, *args, **kwargs)


class TemporaryAdImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing images on temporary ads.
    """

    serializer_class = TemporaryAdImageSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """
        Filter temporary images by the parent temporary ad.
        """
        temp_ad_id = self.kwargs.get("temporary_ad_pk")
        return TemporaryAdImage.objects.filter(temporary_ad_id=temp_ad_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["temp_ad_id"] = self.kwargs.get("temporary_ad_pk")
        return context

    def list(self, request, *args, **kwargs):
        # Extract the temporary ad ID from your nested URL path configuration
        ad_id = self.kwargs.get("temporary_ad_pk")

        # Instantiate the decorator inline to capture the dynamic parent temporary ad ID
        @custom_cache_version(f"temp_ads_images_{ad_id}", timeout=60 * 600)
        def get_cached_temp_images_list(
            inner_self, inner_request, *inner_args, **inner_kwargs
        ):
            return super(TemporaryAdImageViewSet, self).list(request, *args, **kwargs)

        return get_cached_temp_images_list(self, request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        # Fetch the specific TemporaryAdImage instance to extract its unique ID
        obj = self.get_object()

        # Instantiate the decorator inline matching your image-specific cache key
        @custom_cache_version(f"temp_ads_image_{obj.id}", timeout=60 * 60)
        def get_cached_temp_image_detail(
            inner_self, inner_request, *inner_args, **inner_kwargs
        ):
            return super(TemporaryAdImageViewSet, self).retrieve(
                request, *args, **kwargs
            )

        return get_cached_temp_image_detail(self, request, *args, **kwargs)
