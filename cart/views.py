from cart import models as m
from cart.serializer import (
    Cart_Item_Serilaizer,
    CartItemCreate_Serializer,
    Wishlist_serializer,
    WishListData_Serializer,
)
from django.db import transaction
from django.shortcuts import get_object_or_404
from product import models as pmd
from rest_framework import generics, permissions, serializers, status
from rest_framework.pagination import PageNumberPagination
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
                {
                    "total_price": 0,
                    "total_quantity": 0,
                    "msg": "Your cart is empty.",
                },
                status=status.HTTP_200_OK,
            )

        total_price = 0
        for item in cart_item_data:
            total_price += item.quantity * item.product.price

        serializer = Cart_Item_Serilaizer(cart_item_data, many=True)
        return Response(
            {
                "cart_items": serializer.data,
                "total_price": float(total_price),
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


########################################################################################


# this is the class to create the wishlist for the user.
class WishlistCreateView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        serializer = Wishlist_serializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {
                    "msg": "Product added to wishlist successfully.",
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


########################################################################################


# this is the class to see the whishlist of the login user.
class WishlistLoginUserView(APIView, PageNumberPagination):
    renderer_classes = [UserRenderer]
    permission_classes = [permissions.IsAuthenticated]
    page_size = 5

    def get(self, request, format=None):
        user = request.user
        wishlist_data = m.Wishlist.objects.filter(user=user).select_related("product")
        if not wishlist_data.exists():
            return Response(
                {"msg": "Your wishlist is currently empty."},
                status=status.HTTP_200_OK,
            )
        # here adding the pagination part.
        paginated_data = self.paginate_queryset(wishlist_data, request, view=self)
        serializer = WishListData_Serializer(paginated_data, many=True)
        return self.get_paginated_response(
            {
                "data": serializer.data,
                "wishlist_count": wishlist_data.count(),
            },
        )


########################################################################################


# this is the class to delete the wishlist.
class WishlistDeleteView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, format=None):
        wishlist_ids = request.data.get("wishlist_ids", [])
        if not wishlist_ids or not isinstance(wishlist_ids, list):
            return Response(
                {"msg": "Please provide a list of wishlist item IDs."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # now deleting the data.
        delete_count = 0
        not_found_ids = []
        with transaction.atomic():
            for wl_id in wishlist_ids:
                try:
                    wishlist_data = m.Wishlist.objects.get(id=wl_id, user=request.user)
                    wishlist_data.delete()
                    delete_count += 1
                except m.Wishlist.DoesNotExist:
                    not_found_ids.append(wl_id)
            return Response(
                {
                    "msg": f"{delete_count} item(s) removed from wishlist.",
                    **({"not_found_ids": not_found_ids} if not_found_ids else {}),
                },
                status=status.HTTP_200_OK,
            )


########################################################################################


# this is the class to shift the wishlist product into cart item.
class WishlistIntoCartItem(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        items = request.data.get("items", [])
        if not items or not isinstance(items, list):
            return Response(
                {"msg": "Please provide a list of wishlist item IDs."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Confirm it exists and belongs to the logged-in user.
        moved_ids = []
        not_found_ids = []
        out_of_stock_ids = []
        all_present_ids = []

        with transaction.atomic():
            for item in items:
                wl_ids = item.get("wishlist_id")
                quantity = item.get("quantity", 1)
                try:
                    wishlist_data = m.Wishlist.objects.get(id=wl_ids, user=request.user)
                    product_data = wishlist_data.product

                    # Check stock availability
                    if product_data.stock < 1:
                        out_of_stock_ids.append(str(wl_ids))
                        continue

                    # Move to cart: Add or update
                    cart_item, created = m.CartItem.objects.get_or_create(
                        user=request.user,
                        product=product_data,
                        defaults={"quantity": quantity},
                    )

                    # if the product is already present in the cart.
                    if not created:
                        cart_item.quantity += quantity
                        cart_item.save()

                    # Remove from wishlist
                    wishlist_data.delete()
                    moved_ids.append(str(wl_ids))

                except m.Wishlist.DoesNotExist:
                    not_found_ids.append(str(wl_ids))

        return Response(
            {
                "msg": f"{len(moved_ids)} item(s) moved to cart successfully.",
                "moved_ids": moved_ids,
                **({"not_found_ids": not_found_ids} if not_found_ids else {}),
                **({"out_of_stock_ids": out_of_stock_ids} if out_of_stock_ids else {}),
                **({"all_present_ids": all_present_ids} if all_present_ids else {}),
            },
            status=status.HTTP_200_OK,
        )
