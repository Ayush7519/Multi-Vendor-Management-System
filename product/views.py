from django.core.cache import cache
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, render
from product import models
from product import serializer as s
from product.validation import validate_image_file
from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from user.models import VendorProfile

from vendorlink.pagination import MyPageNumberPaginationClass
from vendorlink.permission import IsVendorUser
from vendorlink.render import UserRenderer

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


########################################################################################


# Lists all active products available to users with essential details.
class UserProductList(APIView, PageNumberPagination):
    renderer_classes = [UserRenderer]
    permission_classes = [permissions.AllowAny]
    page_size = 10

    def get(self, request, format=None):
        queryset = models.Product.objects.filter(is_active=True)

        try:
            # Passing data to the paginator
            paginated_queryset = self.paginate_queryset(queryset, request, view=self)

            # Serializing paginated data
            serializer = s.ProductList_Serializer(paginated_queryset, many=True)

            return Response(
                {"data": serializer.data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"msg": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


########################################################################################


# Retrieves product details and increments view count
class SingleProductCustomerView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, product_id, format=None):
        try:
            product_data = models.Product.objects.get(product_id=product_id)
        except models.Product.DoesNotExist:
            raise NotFound(detail="Product not found or does not belong to the vendor.")

        # Here, we will track the viewer and increment the product’s view count accordingly.
        user_id = request.user.user_id
        is_other_vendor = False
        is_customer = False
        cache_key = f"product_view:{user_id}:{product_id}"

        with transaction.atomic():

            # Check if the user has viewed this product recently
            if not cache.get(cache_key):
                try:
                    vendor_profile = models.VendorProfile.objects.get(user=user_id)

                    # Check if the product belongs to this vendor
                    is_own_product = models.Product.objects.filter(
                        product_id=product_id, vendor=vendor_profile
                    ).exists()

                    if not is_own_product:
                        is_other_vendor = True

                except models.VendorProfile.DoesNotExist:
                    is_customer = True

                if is_customer:
                    product_data.views = F("views") + 1
                    product_data.save(update_fields=["views"])
                    product_data.refresh_from_db()

                if is_other_vendor:
                    product_data.vendor_views = F("vendor_views") + 1
                    product_data.save(update_fields=["vendor_views"])
                    product_data.refresh_from_db()

                # Set cache key to prevent increments within next 60 seconds
                cache.set(cache_key, True, timeout=60)

            serializer = s.ProductList_Serializer(product_data)
            return Response(
                {"data": serializer.data},
                status=status.HTTP_200_OK,
            )


########################################################################################


# Handles product search queries to help users find relevant items.
class UserSearchProductView(APIView, PageNumberPagination):
    renderer_classes = [UserRenderer]
    permission_classes = [permissions.AllowAny]
    page_size = 10

    # making the filter function to avoid the code redundancy.

    def filter_data_processing(self, filter_params):
        filter_ids = []
        if filter_params:
            filter_ids = [
                int(fil_ids.strip())
                for fil_ids in filter_params.split(",")
                if fil_ids.strip().isdigit()
            ]
        return filter_ids

    def get(self, request, format=None):
        queryset = models.Product.objects.all()
        print(queryset)
        # Extracting the keyword used for searching products.
        search_query = request.query_params.get("search", "").strip()

        # Searching products if a search query is provided.
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(category__name__icontains=search_query)
                | Q(tags__name__icontains=search_query)
            ).distinct()

        # Filtering products by category.
        category_param = request.query_params.get("category", "").strip()
        # Unpacking individual category IDs from the list.
        if category_param:
            category_ids = self.filter_data_processing(filter_params=category_param)
            if category_ids:
                queryset = queryset.filter(category__in=category_ids)

        # Filtering products by tags.
        tags_param = request.query_params.get("tag", "").strip()
        # Unpacking individual tags IDs from the list.
        if tags_param:
            tags_ids = self.filter_data_processing(filter_params=tags_param)
            if tags_ids:
                queryset = queryset.filter(tags__in=tags_ids)

        # Applies sorting to the product list based on the given parameter.
        sort_param = request.query_params.get("sort", "").strip()
        if sort_param:
            sort_mapping = {
                "price_asc": "price",
                "price_desc": "-price",
                "views_asc": "views",
                "views_desc": "-views",
                "created_at_asc": "created_at",
                "created_at_desc": "-created_at",
                "rating_asc": "average_rating",
                "rating_desc": "-average_rating",
            }
            sort_field = sort_mapping.get(sort_param)
            if sort_field:
                queryset = queryset.order_by(sort_field)

        # Filtering products based on the specified price range.
        min_price_params = request.query_params.get("min_price", "").strip()
        max_price_params = request.query_params.get("max_price", "").strip()

        if min_price_params:
            queryset = queryset.filter(price__gte=min_price_params)

        if max_price_params:
            queryset = queryset.filter(price__lte=max_price_params)

        # here we pass the data to the pagination.
        paginated_data = self.paginate_queryset(queryset, request, view=self)

        serializer = s.ProductList_Serializer(paginated_data, many=True)
        if not serializer.data:
            return Response(
                {"message": "No products found matching your criteria."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return self.get_paginated_response(
            {
                "filters": {
                    "search": search_query,
                    "category_ids": category_ids if category_param else [],
                    "tag_ids": tags_ids if tags_param else [],
                    "sort_by": sort_param,
                    "min_price": min_price_params if min_price_params else None,
                    "max_price": max_price_params if max_price_params else None,
                },
                "results": serializer.data,
            }
        )


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
