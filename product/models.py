import uuid

from django.db import models
from user.models import VendorProfile, customeuser

############################################################################################


# this is the model for the Category.
class Category(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)

    def __str__(self):
        return self.name


############################################################################################


def upload_to(instance, filename):
    return f"product/gallery/{filename}"


# this is the model for the multiple image uploader.
class MultipleImages(models.Model):
    image = models.ImageField(upload_to=upload_to)
    alt_text = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self):
        return self.alt_text or "Product Gallery Image"


############################################################################################


# this is the model for the tags.
class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name


############################################################################################


# this is the model for the product.
class Product(models.Model):
    product_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name="products",
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.TextField(max_length=200, blank=True, null=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="products"
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=False, null=False
    )
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    stock = models.PositiveIntegerField()
    images = models.ManyToManyField(
        MultipleImages,
        blank=True,
        null=True,
    )
    tags = models.ManyToManyField(Tag, blank=True)
    is_active = models.BooleanField(default=True)
    average_rating = models.FloatField(default=0.0)
    total_reviews = models.IntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
