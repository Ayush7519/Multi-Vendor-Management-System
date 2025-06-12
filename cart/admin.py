from cart import models as m
from django.contrib import admin


# Register your models here.
class CartAdmin(admin.ModelAdmin):
    list_display = (
        "cartitem_id",
        "user",
        "product",
        "quantity",
        "created_at",
    )


admin.site.register(m.CartItem, CartAdmin)


# register the model in the admin site.
class Wishlist_Admin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "product",
        "added_at",
    )


admin.site.register(m.Wishlist, Wishlist_Admin)
