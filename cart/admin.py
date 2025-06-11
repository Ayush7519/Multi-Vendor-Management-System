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
