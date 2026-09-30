import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

# ---------------------------------------------------------------------------
# Custom Managers with select_related / prefetch_related
# ---------------------------------------------------------------------------

class CustomerProfileManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("user")


class CategoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("parent")


class ProductManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("category", "supplier")
            .prefetch_related("images")
        )


class SupplierManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("pickup_location")


class PickupLocationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("supplier")


class OrderManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("customer__user", "delivery_location")
            .prefetch_related("items__product")
        )


class OrderItemManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("order", "product", "supplier")


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------

class CustomerProfile(models.Model):
    """
    Customer profile linked to the user model.
    Customers specify where they want their order delivered.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    # Default delivery address for this customer
    default_delivery_address = models.TextField(
        blank=True,
        help_text="Where the customer wants to receive their products.",
    )
    default_delivery_location = models.ForeignKey(
        "DeliveryLocation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_for_customers",
        help_text="Preferred delivery zone/point for this customer.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomerProfileManager()

    class Meta:
        verbose_name = "Customer Profile"
        verbose_name_plural = "Customer Profiles"

    def __str__(self):
        return f"Profile for {self.user.mobile_number}"

    @property
    def whatsapp_link(self):
        if not self.user.mobile_number:
            return "#"
        clean_number = "".join(filter(str.isdigit, self.user.mobile_number))
        clean_number = clean_number.removeprefix("0")
        return f"https://wa.me/{clean_number}"


# ---------------------------------------------------------------------------
# Geography / Locations
# ---------------------------------------------------------------------------

class DeliveryLocation(models.Model):
    """
    A place where customers can receive their orders.
    Could be a neighborhood, town, or specific meeting point in São Tomé.
    """

    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = models.Manager()

    class Meta:
        verbose_name = "Delivery Location"
        verbose_name_plural = "Delivery Locations"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PickupLocation(models.Model):
    """
    A place where suppliers deliver goods, chosen to be closest to each supplier.
    We collect goods from these locations.
    """

    name = models.CharField(max_length=150, unique=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True, help_text="Access notes, hours, contact person.")
    is_active = models.BooleanField(default=True)

    objects = PickupLocationManager()

    class Meta:
        verbose_name = "Pickup Location"
        verbose_name_plural = "Pickup Locations"
        ordering = ["name"]

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------

class Supplier(models.Model):
    """
    A supplier of São Tomé products (mango, cajamanga, safu, maracujá, etc.).
    Each supplier is assigned to the pickup location closest to them.
    """

    name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=150, blank=True)
    mobile_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    pickup_location = models.ForeignKey(
        PickupLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suppliers",
        help_text="The pickup spot closest to this supplier.",
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SupplierManager()

    class Meta:
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"
        ordering = ["name"]

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Categories & Products
# ---------------------------------------------------------------------------

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=10, blank=True, help_text="Emoji or icon for the category"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CategoryManager()

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return f"{self.icon or '📁'} {self.name}"


class Product(models.Model):
    """
    A product sourced from São Tomé (mango, cajamanga, safu, maracujá, etc.).
    Stock is tracked per supplier; we collect from pickup locations.
    """

    class Unit(models.TextChoices):
        KG = "KG", "Quilograma"
        UNIT = "UNIT", "Unidade"
        BUNCH = "BUNCH", "Molho"
        BOX = "BOX", "Caixa"

    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="products"
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True, related_name="products"
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    unit = models.CharField(
        max_length=10, choices=Unit.choices, default=Unit.KG
    )
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Available quantity at the supplier / pickup location.",
    )
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductManager()

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["-is_featured", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"


class ProductImage(models.Model):
    """
    Multiple images per product.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="products/images/")
    api_image_webp = models.ImageField(
        upload_to="products/images_webp/", blank=True, null=True
    )
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Image for {self.product.name}"


# ---------------------------------------------------------------------------
# Orders & Payment
# ---------------------------------------------------------------------------

class OrderStatus(models.TextChoices):
    PENDING_PAYMENT = "PENDING_PAYMENT", "Aguardando Pagamento"
    PAYMENT_VERIFIED = "PAYMENT_VERIFIED", "Pagamento Verificado"
    COLLECTING = "COLLECTING", "Em Recolha nos Fornecedores"
    READY_FOR_DELIVERY = "READY_FOR_DELIVERY", "Pronto para Entrega"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY", "Em Rota de Entrega"
    DELIVERED = "DELIVERED", "Entregue"
    CANCELLED = "CANCELLED", "Cancelado"


def default_expiration_date():
    return timezone.now() + timedelta(days=3)


class Order(models.Model):
    """
    A customer order. Payment is made via bank transfer; the customer
    includes the order number in the transfer reference. We verify with
    the bank before releasing the order.
    """

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(
        CustomerProfile, on_delete=models.PROTECT, related_name="orders"
    )
    delivery_location = models.ForeignKey(
        DeliveryLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    delivery_address = models.TextField(
        help_text="Where the customer wants to receive the products."
    )
    status = models.CharField(
        max_length=30, choices=OrderStatus.choices,
        default=OrderStatus.PENDING_PAYMENT,
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Bank transfer / payment verification
    transfer_reference = models.CharField(
        max_length=100, blank=True,
        help_text="Reference used by the customer in the bank transfer.",
    )
    payment_verified_at = models.DateTimeField(null=True, blank=True)
    payment_verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_orders",
    )

    # Fulfillment timestamps
    expires_at = models.DateTimeField(default=default_expiration_date)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OrderManager()

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.order_number} - {self.customer.user.mobile_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Simple sequential-ish order number; adjust as needed.
            self.order_number = f"STP-{timezone.now():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def recalculate_total(self):
        total = sum(item.subtotal for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=["total_amount"])
        return total


class OrderItem(models.Model):
    """
    A line item in an order. Links to a product and its supplier so we know
    which pickup location to collect from.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="order_items"
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.PROTECT, related_name="order_items"
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    objects = OrderItemManager()

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        ordering = ["order", "product__name"]

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order {self.order.order_number})"

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)