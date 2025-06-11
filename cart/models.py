import uuid

from django.db import models
from product import models as m
from user.models import customeuser

############################################################################################


# this is the class for the cart model.
class CartItem(models.Model):
    cartitem_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    user = models.ForeignKey(
        customeuser,
        on_delete=models.CASCADE,
        related_name="cart_items",
        blank=True,
        null=True,
    )
    product = models.ForeignKey(m.Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "product"], name="unique_cart_item")
        ]

    def __str__(self):
        return f"{self.user.username} - {self.product.name} (x{self.quantity})"
