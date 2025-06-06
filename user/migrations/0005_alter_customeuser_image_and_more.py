# Generated by Django 5.2.1 on 2025-05-25 16:11

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_vendorprofile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customeuser',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='user_profile_picture/'),
        ),
        migrations.AlterField(
            model_name='vendorprofile',
            name='shop_logo',
            field=models.ImageField(blank=True, null=True, upload_to='vender_picture/'),
        ),
        migrations.AlterField(
            model_name='vendorprofile',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vendor_profile', to=settings.AUTH_USER_MODEL),
        ),
    ]
