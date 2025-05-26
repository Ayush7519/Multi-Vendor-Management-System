from rest_framework import serializers


def IMAGE_VALIDATION(img, un):
    ext = img.name.split(".")[-1]
    image_name = un + "." + ext
    if ext.lower() in ("png", "jpeg", "jpg"):
        return image_name
    else:
        raise serializers.ValidationError(
            "Extension Doesnot match.It should be of png,jpg,jpeg"
        )
