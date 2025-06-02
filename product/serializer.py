from product import models
from product.validation import validate_image_file
from rest_framework import serializers
from user.serializer import VendorProfile_Serializer

########################################################################################


# this is the class for the category serializr.
class Category_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        fields = "__all__"


########################################################################################


# this is the class for the category serializr.
class Tags_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = "__all__"


########################################################################################


# this is the class for the category serializr.
class Image_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.MultipleImages
        fields = [
            "image",
            "alt_text",
        ]


########################################################################################


# this is the serializer for the product create.
class ProductCreate_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.Product
        fields = [
            "product_id",
            "vendor",
            "name",
            "description",
            "category",
            "price",
            "discount_price",
            "stock",
            "images",
            "tags",
            "is_active",
            "average_rating",
            "total_reviews",
            "views",
            "created_at",
            "updated_at",
        ]


########################################################################################


# this is the serialiizer for the produce list.
class ProductList_Serializer(serializers.ModelSerializer):
    vendor = VendorProfile_Serializer()
    images = Image_Serializer(many=True)
    tags = Tags_Serializer(many=True)
    category = Category_Serializer()

    class Meta:
        model = models.Product
        fields = [
            "product_id",
            "vendor",
            "name",
            "description",
            "category",
            "price",
            "discount_price",
            "stock",
            "images",
            "tags",
            "is_active",
            "average_rating",
            "total_reviews",
            "views",
            "vendor_views",
            "created_at",
            "updated_at",
        ]


########################################################################################


# this is the serialiizer for the produce list.
class ProductUpdate_Serializer(serializers.ModelSerializer):
    vendor = VendorProfile_Serializer()
    images = Image_Serializer(many=True)
    tags = Tags_Serializer(many=True, read_only=True)
    category = serializers.PrimaryKeyRelatedField(
        queryset=models.Category.objects.all()
    )

    # Adding an additional field to simplify the process of updating stock information.
    added_stock = serializers.IntegerField(min_value=1, required=False)
    subtracted_stock = serializers.IntegerField(min_value=1, required=False)

    # Adding an additional field to simplify the process of updating tags information.
    added_tags = serializers.PrimaryKeyRelatedField(
        queryset=models.Tag.objects.all(), many=True, required=False
    )
    removed_tags = serializers.PrimaryKeyRelatedField(
        queryset=models.Tag.objects.all(), many=True, required=False
    )

    # Adding an additional field to simplify the process of updating image information.
    added_image = serializers.ListField(child=serializers.ImageField(), required=False)
    removed_image = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
    )
    alt_texts = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = models.Product
        fields = [
            "product_id",
            "vendor",
            "name",
            "description",
            "category",
            "price",
            "discount_price",
            "stock",
            "images",
            "tags",
            "is_active",
            "average_rating",
            "total_reviews",
            "views",
            "created_at",
            "updated_at",
            "added_stock",
            "subtracted_stock",
            "added_tags",
            "removed_tags",
            "added_image",
            "removed_image",
            "alt_texts",
        ]

    def validate(self, attrs):
        old_stock = self.instance.stock
        ad_stock = attrs.pop("added_stock", None)
        sub_stock = attrs.pop("subtracted_stock", None)

        # Ensure that the request does not contain both added_stock and subtracted_stock.
        if ad_stock and sub_stock:
            raise serializers.ValidationError(
                "You cannot add and subtract stock at the same time."
            )

        if ad_stock:
            new_stock = int(old_stock) + ad_stock
            attrs["stock"] = new_stock

        if sub_stock:
            new_stock = int(old_stock) - sub_stock
            if new_stock <= 0:
                raise serializers.ValidationError(
                    "Sorry, the new stock cannot be zero or negative."
                )
            attrs["stock"] = new_stock
        return attrs

    # This section handles the updating of the product's associated tags.
    def update(self, instance, validated_data):
        added_tags = validated_data.pop("added_tags", [])
        removed_tags = validated_data.pop("removed_tags", [])

        added_image = validated_data.pop("added_image", [])
        removed_image = validated_data.pop("removed_image", [])
        alt_texts = validated_data.pop("alt_texts", [])

        # Update other fields
        instance = super().update(instance, validated_data)

        # Process and add new images from the request data, validating each image and associating optional alt text
        if added_image:
            for idx, img in enumerate(added_image):
                validate_image_file(img)
                alt_text = alt_texts[idx] if idx < len(alt_texts) else ""
                image_instance = models.MultipleImages.objects.create(
                    image=img, alt_text=alt_text
                )
                instance.images.add(image_instance)

        # Handle deletion of images requested for removal, ensuring only images linked to this product are deleted
        if removed_image:
            for image_id in removed_image:
                try:
                    image = models.MultipleImages.objects.get(id=image_id)
                    if image in instance.images.all():
                        image.delete()
                except models.MultipleImages.DoesNotExist:
                    continue

        # Cache current tags for efficient membership checks
        current_tags = set(instance.tags.all())

        # Add the tags specified in added_tags only if they are not already linked to the product
        for tag in added_tags:
            if tag not in current_tags:
                instance.tags.add(tag)

        # Remove the tags specified in removed_tags only if they are currently associated with the product
        for tag in removed_tags:
            if tag in current_tags:
                instance.tags.remove(tag)

        return instance
