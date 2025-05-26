import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


# this is the custome model for the user login.
class UserManager(BaseUserManager):
    def create_user(
        self,
        email,
        username,
        first_name,
        last_name,
        role,
        phone_number,
        password=None,
        password2=None,
        **extra_fields,
    ):
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
            role=role,
            phone_number=phone_number,
            **extra_fields,
        )
        user.is_active = True
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email,
        username,
        password,
        first_name,
        last_name,
        phone_number,
        **extra_fields,
    ):
        if not email:
            raise ValueError("Users must have an email address")

        user = self.create_user(
            email=self.normalize_email(email),
            password=password,
            username=username,
            first_name=first_name,
            last_name=last_name,
            role="A",
            phone_number=phone_number,
        )
        user.is_admin = True
        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class customeuser(AbstractBaseUser):
    ROLE_CHOICE = [
        ("A", "Admin"),
        ("C", "Customer"),
        ("V", "Vendor"),
    ]
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, blank=False, unique=True)
    email = models.EmailField(
        verbose_name="E-mail",
        max_length=255,
        unique=True,
    )
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(blank=True, max_length=50)
    role = models.CharField(max_length=10, choices=ROLE_CHOICE, default="A")
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    phone_number = PhoneNumberField(region="NP", blank=True, null=True)
    image = models.ImageField(upload_to="user_profile_picture/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name", "phone_number"]

    @property
    def id(self):
        return self.user_id

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return self.is_admin

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

    def __str__(self):
        return self.username


# this is the model for the vendor profile(additional data.)
class VendorProfile(models.Model):
    user = models.OneToOneField(
        customeuser,
        on_delete=models.CASCADE,
        related_name="vendor_profile",
        blank=True,
        null=True,
    )
    shop_name = models.CharField(max_length=100, blank=False, null=False)
    shop_logo = models.ImageField(upload_to="vender_picture/", blank=True, null=True)
    descriptioin = models.TextField(max_length=500, blank=True, null=True)
    address = models.CharField(max_length=100, blank=False, null=False)
    phone_number = PhoneNumberField(region="NP", blank=False, null=False)
    website = models.URLField(max_length=100, blank=True, null=True)
    gst_number = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username
