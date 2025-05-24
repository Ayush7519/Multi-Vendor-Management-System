from django.contrib import admin
from user import models


# registration of the model in the admin pannel.
class customeuseradminmodel(admin.ModelAdmin):
    list_display = (
        "user_id",
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "date_joined",
        "is_active",
        "is_superuser",
        "is_staff",
        "phone_number",
        "image",
        "is_verified",
    )


admin.site.register(models.customeuser, customeuseradminmodel)
