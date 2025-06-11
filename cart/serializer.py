from cart import models as m
from product import models as pm
from product import models as pmd
from product.serializer import ProductList_Serializer
from rest_framework import serializers, status
from rest_framework.response import Response
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

    class Meta:
        model = m.CartItem
        fields = (
            "cartitem_id",
            "product",
            "quantity",
            "created_at",
        )
