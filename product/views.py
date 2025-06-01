from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from product import models
from product import serializer as s
from product.validation import validate_image_file
from rest_framework import generics, permissions, serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from user.models import VendorProfile

from vendorlink.pagination import MyPageNumberPaginationClass
from vendorlink.permission import IsVendorUser
from vendorlink.render import UserRenderer

########################################################################################


# this is the  view to create the category.
class CategoryCreateView(generics.CreateAPIView):
    permission_classes = [IsVendorUser]
    renderer_classes = [UserRenderer]
    serializer_class = s.Category_Serializer
    queryset = models.Category.objects.all()


########################################################################################


# this is the class to list all the category to create the product.
class CategoryListView(generics.ListAPIView):
    permission_classes = [IsVendorUser]
    renderer_classes = [UserRenderer]
    serializer_class = s.Category_Serializer
    queryset = models.Category.objects.all()


########################################################################################


# this is the class for the category update.
class CategoryUpdateView(generics.UpdateAPIView):
    permission_classes = [IsVendorUser]
    renderer_classes = [UserRenderer]
    serializer_class = s.Category_Serializer
    queryset = models.Category.objects.all()


########################################################################################


# this is the class for the category delete.
class CategoryDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAdminUser]
    renderer_classes = [UserRenderer]
    serializer_class = s.Category_Serializer
    queryset = models.Category.objects.all()


########################################################################################


# this is the  view to create the tags.
class TagsCreateView(generics.CreateAPIView):
    permission_classes = [IsVendorUser]
    renderer_classes = [UserRenderer]
    serializer_class = s.Tags_Serializer
    queryset = models.Tag.objects.all()


########################################################################################


# this is the  view to list the tags.
class TagsListView(generics.ListAPIView):
    permission_classes = [IsVendorUser]
    renderer_classes = [UserRenderer]
    serializer_class = s.Tags_Serializer
    queryset = models.Tag.objects.all()


########################################################################################


# this is the  view to update the tags.
class TagsUpdateView(generics.UpdateAPIView):
    permission_classes = [IsVendorUser]
    renderer_classes = [UserRenderer]
    serializer_class = s.Tags_Serializer
    queryset = models.Tag.objects.all()


########################################################################################


# this is the  view to create the tags.
class TagsDeleteView(generics.DestroyAPIView):
    permission_classes = [IsVendorUser]
    renderer_classes = [UserRenderer]
    serializer_class = s.Tags_Serializer
    queryset = models.Tag.objects.all()


########################################################################################


###here the tags handeling feature is to be added soon.
# this is the class for the product create.
class ProductCreateView(APIView):
    permission_classes = [IsVendorUser]
    renderer_classes = [UserRenderer]

    def post(self, request, format=None):
        pro_fields = s.ProductCreate_Serializer.Meta.fields

        # Separate incoming data
        product_data_dict = {k: v for k, v in request.data.items() if k in pro_fields}
        product_serializer = s.ProductCreate_Serializer(data=product_data_dict)

        images_files = request.FILES.getlist("image")  # ✅ Get multiple images
        alt_texts = request.data.get("alt_text", "")  # Optional alt text for all

        # counting the number of images.
        if len(images_files) > 5:
            return Response(
                {"detail": "You can upload up to 5 images per product."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            if product_serializer.is_valid(raise_exception=True):
                # Save the product and assign vendor
                login_user = get_object_or_404(
                    VendorProfile, user_id=request.user.user_id
                )
                product_instance = product_serializer.save(vendor=login_user)

                # ✅ Save each image and add to product
                for idx, img in enumerate(images_files):
                    validate_image_file(img)
                    alt_text = alt_texts[idx] if idx < len(alt_texts) else ""
                    image_instance = models.MultipleImages.objects.create(
                        image=img, alt_text=alt_text
                    )
                    product_instance.images.add(image_instance)

                # Re-serialize product instance to return the updated data
                response_data = s.ProductCreate_Serializer(product_instance).data

                return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(
            {"product_errors": product_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


########################################################################################


# this is the class Allow vendors to retrieve a paginated list of all products they have created.
class VendorProductListView(APIView, PageNumberPagination):
    renderer_classes = [UserRenderer]
    permission_classes = [IsVendorUser]
    page_size = 10

    def get(self, request, format=None):
        user = request.user.user_id
        vendor_profile = get_object_or_404(models.VendorProfile, user=user)

        search_query = request.query_params.get("search", "").strip()
        sort_query = request.query_params.get("sort", "").strip()

        queryset = models.Product.objects.filter(vendor=vendor_profile)

        # Apply search filter if search_query is provided
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(category__name__icontains=search_query)
                | Q(tags__name__icontains=search_query)
            ).distinct()

        # Map sort query param to model fields
        sort_mapping = {
            "name_asc": "name",
            "name_desc": "-name",
            "price_asc": "price",
            "price_desc": "-price",
            "created_at_asc": "created_at",
            "created_at_desc": "-created_at",
            "stock_asc": "stock",
            "stock_desc": "-stock",
            "rating_asc": "average_rating",
            "rating_desc": "-average_rating",
        }
        sort_field = sort_mapping.get(sort_query)

        # Apply sorting if valid sort param is provided
        if sort_field:
            queryset = queryset.order_by(sort_field)

        # Paginate queryset
        paginated_queryset = self.paginate_queryset(queryset, request, view=self)

        # Serialize paginated data
        serializer = s.ProductList_Serializer(paginated_queryset, many=True)

        # Return paginated response
        return self.get_paginated_response(serializer.data)


########################################################################################


# this is the class to  Retrieve Single Product (Owned by Vendor)
class VendorSingleProductDetailView(generics.RetrieveAPIView):
    renderer_classes = [UserRenderer]
    permission_classes = [permissions.IsAuthenticated, IsVendorUser]
    serializer_class = s.ProductList_Serializer
    lookup_field = "product_id"

    def get_queryset(self):
        return models.Product.objects.all()


########################################################################################


# this is the class to delete the product by the vendor.
class VendorProductDeleteView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsVendorUser]

    def delete(self, request, product_id, format=None):
        print(product_id)
        user = request.user.user_id

        # now checking if the user has vendor profile or not
        vendor_profile = get_object_or_404(VendorProfile, user=user)

        # Try to get the product associated with this vendor and the given product_id
        try:
            delete_product = models.Product.objects.get(
                vendor=vendor_profile, product_id=product_id
            )
        except models.Product.DoesNotExist:
            return Response(
                {"error": "Product not found or does not belong to the vendor."},
                status=status.HTTP_404_NOT_FOUND,
            )
        with transaction.atomic():
            delete_product.delete()  # this will delete the product from the data base.

        return Response(
            {"message": "Product has been successfully deleted"},
            status=status.HTTP_200_OK,
        )


########################################################################################


# this is the class to update the data of the product.(can only done by the vendor).
class VendorProductUpdateView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsVendorUser]

    # Handles full update (PUT) of product data
    def put(self, request, product_id, format=None):
        return self.update_product_data(request, product_id, partial=False)

    # Handles partial update (PATCH) of product data
    def patch(self, request, product_id, format=None):
        return self.update_product_data(request, product_id, partial=True)

    # It ensures that only the vendor who owns the product can modify its data.
    def update_product_data(self, request, product_id, partial):

        # Check if the logged-in user has an associated vendor profile
        try:
            user_profile_check = models.VendorProfile.objects.get(
                user=request.user.user_id
            )
        except models.VendorProfile.DoesNotExist:
            return Response(
                {"error": "user not found or does not belong to the vendor profile."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Verify that the requested product belongs to the currently authenticated vendor.
        try:
            product_data = models.Product.objects.get(
                vendor=user_profile_check, product_id=product_id
            )
            print(product_data)
        except models.Product.DoesNotExist:
            return Response(
                {"error": "Product not found or does not belong to the vendor."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # here sending the data to the serializer.
        serializer = s.ProductUpdate_Serializer(
            product_data, data=request.data, partial=partial
        )

        if serializer.is_valid(raise_exception=True):
            with transaction.atomic():
                serializer.save()
                return Response(
                    {
                        "message": "Product updated successfully.",
                        "product": serializer.data,
                    },
                    status=200,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
