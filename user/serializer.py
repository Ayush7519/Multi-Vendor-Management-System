from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.encoding import DjangoUnicodeDecodeError, force_bytes, smart_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers, status
from user import models

from vendorlink.utils import Util


# this is the class for the user registration.
class UserRegistration_Serializer(serializers.ModelSerializer):
    password2 = serializers.CharField(
        style={"input_type": "password", "write_only": True}
    )

    class Meta:
        model = models.customeuser
        fields = "__all__"
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):
        password = attrs.get("password")
        password2 = attrs.get("password2")
        if password != password2:
            raise serializers.ValidationError(
                "Password and Confirm password should be same"
            )
        return super().validate(attrs)

    def create(self, validated_data):
        return models.customeuser.objects.create_user(**validated_data)


#########################################################################################


# this is for the user login part.
class UserLogin_Serializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)

    class Meta:
        model = models.customeuser
        fields = ["email", "password"]


#########################################################################################


# this is form the vendor verified.
class CustomeUser_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.customeuser
        fields = "__all__"


#########################################################################################


# this is for the vender profile create.
class VendorProfile_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.VendorProfile
        fields = [
            "shop_name",
            "shop_logo",
            "descriptioin",
            "address",
            "phone_number",
            "website",
            "gst_number",
            "created_at",
            "updated_at",
        ]


#########################################################################################


# this is for the full user detail in the admin pannel.
class CustomeUserDetail_Serializer(serializers.ModelSerializer):
    vendor_profile = VendorProfile_Serializer()

    class Meta:
        model = models.customeuser
        fields = [
            "user_id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "date_joined",
            "is_active",
            "is_admin",
            "is_superuser",
            "is_staff",
            "phone_number",
            "image",
            "is_verified",
            "vendor_profile",
        ]


#########################################################################################


# this is the class for the serializer of the vendor profile.
class VendorProfileUpdate_Serilaizer(serializers.ModelSerializer):
    class Meta:
        model = models.VendorProfile
        fields = "__all__"


#########################################################################################


# this is the class for the user password change.
class UserPasswordChange_Serializer(serializers.ModelSerializer):
    old_password = serializers.CharField(required=True)
    password = serializers.CharField(
        max_length=255, style={"input_type": "password"}, write_only=True
    )
    password2 = serializers.CharField(
        max_length=255, style={"input_type": "password"}, write_only=True
    )

    class Meta:
        model = models.customeuser
        fields = ["old_password", "password", "password2"]

    def validate(self, attrs):
        try:
            oldpass = attrs.get("old_password")
            fpass = attrs.get("password")
            spass = attrs.get("password2")
            user = self.context.get("user")

            if not oldpass or not fpass or not spass:
                raise serializers.ValidationError(
                    {"error": "Old_Password, Password and Password2 are required."}
                )

            if not user.check_password(oldpass):
                raise serializers.ValidationError(
                    {"error": "Old password is incorrect."}
                )

            if fpass != spass:
                raise serializers.ValidationError(
                    {"error": "Password and Confirm password doesnot matches..."}
                )

            with transaction.atomic():
                user.set_password(fpass)
                user.save()

                # sending the mail to the user after the password is changed.
                data = {
                    "subject": "Password Changed Successfully -Vendora!",
                    "body": f"Hi {user.username},\n\n"
                    "We wanted to let you know that your account password has been successfully changed.\n\n"
                    "If you did not make this change, please contact our support team immediately.\n\n"
                    "Thank you,\n"
                    "The Vendora Team",
                    "to_email": user.email,
                }
                Util.send_email(data)
            return attrs
        except Exception as e:
            raise serializers.ValidationError(
                {"error": f"An unexpected error occurred: {str(e)}"}
            )


#########################################################################################


# this is the serializer to send the mail to the user for password change.
class LinkSendingUser_Serializer(serializers.ModelSerializer):
    email = serializers.EmailField()

    class Meta:
        model = models.customeuser
        fields = ["email"]

    def validate(self, attrs):
        em = attrs.get("email")
        try:
            if models.customeuser.objects.filter(email=em).exists():
                with transaction.atomic():
                    user_data = models.customeuser.objects.get(email=em)
                    uid = urlsafe_base64_encode(force_bytes(user_data.user_id))
                    token = PasswordResetTokenGenerator().make_token(user_data)
                    link = "http://127.0.0.1:3000/user/reset/" + uid + "/" + token

                    # now making the mail data.
                    context = {
                        "subject": "Reset Your Password - Vendora",
                        "username": user_data.username,
                        "reset_link": link,
                        "plain_text": f"Dear {user_data.username}, Please reset your password here: {link}",
                    }

                    Util.send_email1(
                        subject=context["subject"],
                        to_email=user_data.email,
                        template_name="emails/password_reset.html",
                        context=context,
                    )

                return attrs
            else:
                raise serializers.ValidationError("Your Email not found")
        except Exception as e:
            raise serializers.ValidationError(
                {"error": f"An unexpected error occurred: {str(e)}"}
            )


#########################################################################################


# this is the class for the password change through the mail.
class UserPasswordChangeMail_serializer(serializers.ModelSerializer):
    password = serializers.CharField(
        max_length=255, style={"input_type": "password"}, write_only=True
    )
    password2 = serializers.CharField(
        max_length=255, style={"input_type": "password"}, write_only=True
    )

    class Meta:
        model = models.customeuser
        fields = ["password", "password2"]

    def validate(self, attrs):
        try:
            uid = self.context.get("uid")
            token = self.context.get("token")
            password = attrs.get("password")
            password2 = attrs.get("password2")

            # checking if both field contain value or not.
            if not password or not password2:
                raise serializers.ValidationError(
                    {"error": "Both password fields are required."}
                )

            if password != password2:
                raise serializers.ValidationError(
                    {"error": "Password and Confirm Password do not match."}
                )

            user_id = smart_str(urlsafe_base64_decode(uid))
            user_data = get_object_or_404(models.customeuser, user_id=user_id)
            if not PasswordResetTokenGenerator().check_token(user_data, token):
                raise serializers.ValidationError(
                    {"error": "Token is not valid or Expired"}
                )
            with transaction.atomic():
                user_data.set_password(password)
                user_data.save()
                data = {
                    "subject": "Password Changed Successfully -Vendora!",
                    "body": f"Hi {user_data.username},\n\n"
                    "We wanted to let you know that your account password has been successfully changed.\n\n"
                    "If you did not make this change, please contact our support team immediately.\n\n"
                    "Thank you,\n"
                    "The Vendora Team",
                    "to_email": user_data.email,
                }
                Util.send_email(data)
            return attrs
        except DjangoUnicodeDecodeError as identifier:
            PasswordResetTokenGenerator().check_token(user_data, token)
            raise serializers.ValidationError("Token is not valid or Expired")
