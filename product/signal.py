import os

from django.db.models.signals import pre_delete
from django.dispatch import receiver
from product.models import MultipleImages, Product


@receiver(pre_delete, sender=Product)
def delete_product_images(sender, instance, **kwargs):
    for image in instance.images.all():
        if image.image and os.path.isfile(image.image.path):
            os.remove(image.image.path)
        image.delete()
