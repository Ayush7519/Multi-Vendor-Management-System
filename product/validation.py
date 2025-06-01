from rest_framework.exceptions import ValidationError

ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]


def validate_image_file(image):
    ext = image.name.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Invalid image format: .{ext}. Only jpg, jpeg, png, webp allowed."
        )
