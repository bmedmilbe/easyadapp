# project/urls.py
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ads.views import AdvertisementViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'ads', AdvertisementViewSet, basename='ad')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/', include('core.urls')),  # Auth endpoints
]