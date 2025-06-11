from cart import views
from django.urls import path

urlpatterns = [
    path(
        "cart-item/create/",
        views.CartItemCreate.as_view(),
        name="path to create the cart product for the user",
    ),
    path(
        "cart-item/list/login-user/",
        views.CartItemViewLoginUser.as_view(),
        name="path to see the cart item of the login user",
    ),
    path(
        "cart-item/delete/",
        views.Cart_Item_Delete_View.as_view(),
        name="path to delete the cart item",
    ),
    path(
        "cart-item/update/<uuid:cart_id>/",
        views.Cart_ItemUpdateView.as_view(),
        name="path to update the cart data",
    ),
]
