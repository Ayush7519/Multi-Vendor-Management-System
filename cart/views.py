from cart import models as m
from cart.serializer import Cart_Item_Serilaizer, CartItemCreate_Serializer
from django.db import transaction
from product import models as pmd
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from vendorlink.render import UserRenderer

########################################################################################


# this is the class for the cart item create.
class CartItemCreate(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        serializer = CartItemCreate_Serializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid(raise_exception=True):
            with transaction.atomic():
                product = serializer.validated_data["product"]
                quantity = serializer.validated_data.get("quantity", 1)

                # Check if the cart item already exists
                cart_exists = m.CartItem.objects.filter(
                    user=request.user, product=product
                ).first()

                if cart_exists:
                    # Just update the quantity
                    cart_exists.quantity += quantity
                    cart_exists.save()

                    return Response(
                        {
                            "msg": "This product is already in your cart. We've increased its quantity."
                        },
                        status=status.HTTP_200_OK,
                    )

                # If not exists, create new cart item
                serializer.save(user=request.user)
                return Response(
                    {"msg": "Item added to cart successfully."},
                    status=status.HTTP_201_CREATED,
                )


########################################################################################


# this is the class to see the cart item of the login user.
class CartItemViewLoginUser(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        cart_item_data = m.CartItem.objects.filter(user=request.user)
        print(cart_item_data)
        if not cart_item_data.exists():
            return Response(
                {"cart_items": [], "msg": "Your cart is empty."},
                status=status.HTTP_200_OK,
            )
        serializer = Cart_Item_Serilaizer(cart_item_data, many=True)
        return Response(
            {
                "cart_items": serializer.data,
                "total_items": cart_item_data.count(),
            }
        )


########################################################################################


# this is the class to delete the cart item by the user.
class Cart_Item_Delete_View(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, format=None):
        cart_item_ids = request.data.get("cartitem_ids", [])
        if not cart_item_ids or not isinstance(cart_item_ids, list):
            return Response(
                {"msg": "Please provide a list of cart item IDs."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        deleted_count = 0
        not_found_ids = []

        # now we delete the data form the data base.
        with transaction.atomic():
            for cart_id in cart_item_ids:
                try:
                    cart_item = m.CartItem.objects.get(
                        cartitem_id=cart_id, user=request.user
                    )
                    cart_item.delete()
                    deleted_count += 1
                except m.CartItem.DoesNotExist:
                    not_found_ids.append(cart_id)

        return Response(
            {
                "msg": f"{deleted_count} item(s) removed from cart.",
                "not_found_ids": not_found_ids if not_found_ids else None,
            },
            status=status.HTTP_200_OK,
        )


########################################################################################


# this is the class to update the cart item data.
class Cart_ItemUpdateView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, cart_id, format=None):
        return self.update(request, cart_id, partial=True)

    def update(self, request, cart_id, partial):
        with transaction.atomic():
            # checking if the cart_item belong to the requested user or not.
            try:
                cart_check = m.CartItem.objects.get(
                    user=request.user, cartitem_id=cart_id
                )
            except m.CartItem.DoesNotExist:
                return Response(
                    {"msg": "Cart item not found or doesn't belong to you."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # checking if the quantity is valid or not.
            new_quantity = request.data.get("quantity")
            if (
                not new_quantity
                or not isinstance(new_quantity, int)
                or new_quantity < 1
            ):
                return Response(
                    {"msg": "Please provide a valid quantity (minimum 1)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verifying availability of the requested quantity in stock.
            product = cart_check.product
            if new_quantity > product.stock:
                return Response(
                    {"msg": f"Only {product.stock} items available in stock."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cart_check.quantity = new_quantity
            cart_check.save()
            return Response(
                {
                    "msg": "Cart item quantity updated successfully.",
                    "cartitem_id": str(cart_check.cartitem_id),
                    "updated_quantity": cart_check.quantity,
                    "product": product.name,
                },
                status=status.HTTP_202_ACCEPTED,
            )
