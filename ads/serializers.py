from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import (
    Ad,
    AdImage,
    Category,
    CustomerProfile,
    TemporaryAd,
    TemporaryAdImage,
)


class CustomerProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for CustomerProfile with whatsapp_link as read-only.
    """
    whatsapp_link = serializers.ReadOnlyField()
    mobile_number = serializers.CharField(source='user.mobile_number', read_only=True)
    district = serializers.CharField(source='user.district', read_only=True)
    
    class Meta:
        model = CustomerProfile
        fields = ['id', 'mobile_number', 'district', 'whatsapp_link', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.
    """
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'description']
        read_only_fields = ['id', 'slug']


class AdImageSerializer(serializers.ModelSerializer):
    """
    Serializer for AdImage model.
    """
    class Meta:
        model = AdImage
        fields = ['id', 'image', 'caption', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class AdCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for Ad model with nested images.
    """
    temp_ad_id = serializers.UUIDField()
    
    class Meta:
        model = Ad
        fields = ['id', 'temp_ad_id']
        read_only_fields = ['id']
    
    def validate(self, attrs):
        """
        Ensure the temporary ad data is fully valid before allowing the conversion.
        """
        try:
            # Optimized: Single DB hit instead of evaluating .exists() and .first() separately
            temp = TemporaryAd.objects.get(pk=attrs['temp_ad_id'])
        except TemporaryAd.DoesNotExist:
            raise ValidationError({"detail": "Temp AD not found!"})

        if not temp.product_name:
            raise ValidationError({"detail": "Temp AD or product name not found!"})

        if not temp.category:
            raise ValidationError({"category": "Category is required."})

        if temp.price is None or temp.price <= 0:
            raise ValidationError({"price": "A valid price is required."})

        if not temp.temporary_images.exists():
            raise ValidationError({"images": "At least one image is required."})

        return attrs
    
    def create(self, validated_data):
        """
        Create a new ad from temp ad with the customer context.
        """
        # Safe access to profile via user context injected into views
        customer_id = self.context.get('customer_id')
        if not customer_id:
            raise ValidationError({"detail": "Authentication required."})

        try:
            customer = CustomerProfile.objects.get(pk=customer_id)
        except CustomerProfile.DoesNotExist:
            raise ValidationError({"detail": "User profile not found. Complete your profile before publishing."})
            
        temp_ad = TemporaryAd.objects.get(pk=validated_data["temp_ad_id"])

        return temp_ad.transfer_to_official_ad(customer_profile=customer)


class AdSerializer(serializers.ModelSerializer):
    """
    Serializer for Ad model with nested images.
    """
    images = AdImageSerializer(many=True, read_only=True)
    customer = CustomerProfileSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    
    class Meta:
        model = Ad
        fields = [
            'id', 'customer', 'category', 'product_name', 'description', 
            'price', 'status', 'is_featured', 'expires_at', 
            'created_at', 'updated_at', 'images'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TemporaryAdImageSerializer(serializers.ModelSerializer):
    """
    Serializer for TemporaryAdImage model.
    """
    class Meta:
        model = TemporaryAdImage
        fields = ['id', 'image', 'caption', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        ad_id = self.context["temp_ad_id"]
        validated_data["temporary_ad_id"] = ad_id
        return super().create(validated_data)


class TemporaryAdSerializer(serializers.ModelSerializer):
    """
    Serializer for TemporaryAd - guest user flow.
    """
    temporary_images = TemporaryAdImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = TemporaryAd
        fields = [
            'id', 'category', 'product_name', 
            'description', 'price', 'temporary_images', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
