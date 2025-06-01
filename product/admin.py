from django.contrib import admin
from product import models as m

# Register your models here.


class imageAdmin(admin.ModelAdmin):
    list_display = ["id", "image", "alt_text"]


admin.site.register(m.MultipleImages, imageAdmin)


admin.site.register(m.Product)
admin.site.register(m.Tag)
