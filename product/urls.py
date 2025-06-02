from django.urls import include, path
from product import views

urlpatterns = [
    path(
        "category/create/",
        views.CategoryCreateView.as_view(),
        name="path to create the category",
    ),
    path(
        "category/list/",
        views.CategoryListView.as_view(),
        name="path to list the category",
    ),
    path(
        "category/update/<int:pk>/",
        views.CategoryUpdateView.as_view(),
        name="path to update the category",
    ),
    path(
        "category/delete/<int:pk>/",
        views.CategoryDeleteView.as_view(),
        name="path to delete the category",
    ),
    ##############################################################################################
    path(
        "tags/create/",
        views.TagsCreateView.as_view(),
        name="path to create the tags",
    ),
    path(
        "tags/list/",
        views.TagsListView.as_view(),
        name="path to list the tags",
    ),
    path(
        "tags/update/<int:pk>/",
        views.TagsUpdateView.as_view(),
        name="path to update the tags",
    ),
    path(
        "tags/delete/<int:pk>/",
        views.TagsDeleteView.as_view(),
        name="path to delete the tags",
    ),
    ##############################################################################################
    path(
        "product/create/",
        views.ProductCreateView.as_view(),
        name="path to create the product",
    ),
    path(
        "vendor-product/list/",
        views.VendorProductListView.as_view(),
        name="path to list the product of the login user",
    ),
    path(
        "vendor-product/single-detail/<uuid:product_id>/",
        views.VendorSingleProductDetailView.as_view(),
        name="path to rtrive the single product.",
    ),
    path(
        "vendor-product/delete/<uuid:product_id>/",
        views.VendorProductDeleteView.as_view(),
        name="path to delete the single product.",
    ),
    path(
        "vendor-product/update/<uuid:product_id>/",
        views.VendorProductUpdateView.as_view(),
        name="path to update the single product by the vendor only.",
    ),
    ##############################################################################################
    path(
        "customer/product-list/",
        views.UserProductList.as_view(),
        name="path to see all the products of the vendor in the website",
    ),
    path(
        "customer/product-detail-view/<uuid:product_id>/",
        views.SingleProductCustomerView.as_view(),
        name="path to see the detail data of the product",
    ),
    path(
        "customer/product-search/",
        views.UserSearchProductView.as_view(),
        name="path to search the product for the customer",
    ),
]
