from cart import models as m
from django.db import transaction
from product import models as pmd
from product.serializer import ProductList_Serializer
from rest_framework import serializers, status
from rest_framework.response import Response
from user.models import VendorProfile
from user.serializer import CustomeUserDetail_Serializer

########################################################################################


# this is the class for the cart serializer.
class CartItemCreate_Serializer(serializers.ModelSerializer):
    product = serializers.UUIDField()

    class Meta:
        model = m.CartItem
        fields = ("cartitem_id", "product", "quantity", "created_at", "updated_at")
        read_only_fields = ("cartitem_id", "created_at", "updated_at")

    def validate(self, attrs):
        # extracting the product if form the respond.
        product_id = attrs.get("product")
        user = self.context["request"].user
        quantity = attrs.get("quantity") or 1

        # checking if the product is present or not.
        try:
            product_data = pmd.Product.objects.get(product_id=product_id)
        except pmd.Product.DoesNotExist:
            raise serializers.ValidationError(
                {"msg": "Product not found"},
            )

        attrs["product"] = product_data

        # checking if the requested stock is present of not.
        if product_data.stock < quantity:
            raise serializers.ValidationError(
                {"msg": f"Only {product_data.stock} items available in stock"}
            )
        attrs["quantity"] = quantity
        return attrs


########################################################################################


# this is the basic serializer for the cart item list.
class Cart_Item_Serilaizer(serializers.ModelSerializer):
    product = ProductList_Serializer()
    # total_price = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = m.CartItem
        fields = (
            "cartitem_id",
            "product",
            "quantity",
            "created_at",
        )


########################################################################################


# this is the class serializer for the wishlist create.
class Wishlist_serializer(serializers.ModelSerializer):
    product = serializers.UUIDField()

    class Meta:
        model = m.Wishlist
        fields = (
            "user",
            "product",
            "added_at",
        )
        read_only_fields = (
            "user",
            "added_at",
        )

    def validate(self, attrs):
        user = self.context["request"].user
        product = attrs.get("product")

        # checking if the product is present or not.
        try:
            product_data = pmd.Product.objects.get(product_id=product)
        except pmd.Product.DoesNotExist:
            raise serializers.ValidationError(
                {"msg": "product cannot be found in the data base"}
            )

        # checking of the product is already in the wishlist or not.
        if m.Wishlist.objects.filter(user=user, product=product_data).exists():
            raise serializers.ValidationError(
                {"msg": "The product is already in your wishlist."}
            )

        # checking if the product belong to the login user or not.
        try:
            user_instance = VendorProfile.objects.get(user=user)
        except:
            user_instance = None

        if user_instance is not None:
            if product_data.vendor == user_instance:
                raise serializers.ValidationError(
                    {"msg": "You do not have permission to access this product."}
                )
        attrs["product"] = product_data
        attrs["user"] = user
        return attrs


########################################################################################


# this is the class for the wishlist data.
class WishListData_Serializer(serializers.ModelSerializer):
    product = ProductList_Serializer()

    class Meta:
        model = m.Wishlist
        fields = (
            "id",
            "product",
            "added_at",
        )
