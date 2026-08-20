from django.urls import include, path
from rest_framework_nested.routers import DefaultRouter, NestedSimpleRouter

from .views import (
    AdImageViewSet,
    AdManageViewSet,
    AdViewViewSet,
    CategoryViewSet,
    TemporaryAdImageViewSet,
    TemporaryAdViewSet,
)

app_name = 'ads'

router = DefaultRouter()

router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'ads', AdViewViewSet, basename='ad-view')
router.register(r'manage/ads', AdManageViewSet, basename='ad-manage')
router.register(r'guest/temporary-ads', TemporaryAdViewSet, basename='temporary-ad') 

# Nested routing for official Ad images -> /ads/{ad_pk}/images/
ads_router = NestedSimpleRouter(router, r'ads', lookup='ad')
ads_router.register(r'images', AdImageViewSet, basename='ad-image')

# Nested routing for guest Ad images -> /guest/temporary-ads/{temporary_ad_pk}/images/
temp_ads_router = NestedSimpleRouter(router, r'guest/temporary-ads', lookup='temporary_ad')
temp_ads_router.register(r'images', TemporaryAdImageViewSet, basename='temporary-ad-image')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(ads_router.urls)),
    path('', include(temp_ads_router.urls)),
]
