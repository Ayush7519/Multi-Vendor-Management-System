from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from user.models import VendorProfile, customeuser
from user.serializer import (
    CustomeUser_Serializer,
    CustomeUserDetail_Serializer,
    LinkSendingUser_Serializer,
    UserLogin_Serializer,
    UserPasswordChange_Serializer,
    UserPasswordChangeMail_serializer,
    UserRegistration_Serializer,
    VendorProfile_Serializer,
    VendorProfileUpdate_Serilaizer,
)

from vendorlink.render import UserRenderer
from vendorlink.throttle import ForgotPasswordRateThrottle
from vendorlink.utils import Util
from vendorlink.validation import IMAGE_VALIDATION


# this function is used to make the token for the user.
def user_generate_token(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


###################################################################################


# this is the class for the user registration.
class UserRegistrationView(APIView):
    renderer_classes = [UserRenderer]

    def post(self, request, format=None):
        serializer = UserRegistration_Serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            # here we perform validation of the image.
            image = request.FILES.get("image")
            username = serializer.validated_data.get("username")
            user_role = serializer.validated_data.get("role")
            try:
                image_name = IMAGE_VALIDATION(image, username)
                serializer.validated_data["image"] = image_name
                with transaction.atomic():
                    user = serializer.save()
                    if user_role in ("C", "A"):
                        context = {
                            "subject": "Welcome to Vendora!",
                            "username": user.username,
                            "plain_text": f"Hello {user.username}, Thank you for registering on Vendora! Your account has been successfully created.",
                        }

                        Util.send_email1(
                            subject=context["subject"],
                            to_email=user.email,
                            template_name="emails/welcome_email.html",
                            context=context,
                        )
                    else:
                        context = {
                            "subject": "Vendor Registration Received - Vendora!",
                            "username": user.username,
                            "body_text": (
                                "Thank you for submitting your registration request to join Vendora!\n\n"
                                "We have received your application and it is currently under review by our team.\n"
                                "Our verification process ensures that all vendor accounts meet the quality and compliance standards of our platform.\n\n"
                                "You will receive a confirmation email once your vendor account has been approved.\n"
                                "This typically takes up to 24–48 hours.\n\n"
                                "We appreciate your patience and look forward to partnering with you."
                            ),
                            "signature": (
                                "Warm regards,\n"
                                "Vendor Support Team\n"
                                "The Vendora Team"
                            ),
                        }

                        Util.send_email1(
                            subject=context["subject"],
                            to_email=user.email,
                            template_name="emails/vendor_registration_received.html",
                            context=context,
                        )

                token = user_generate_token(user)
                return Response(
                    {
                        "token": token,
                        "msg": "Registration Successful",
                    },
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    {"error": "Registration failed: " + str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#########################################################################################


# this is the class for the user login.
class UserLoginView(APIView):
    renderer_classes = [UserRenderer]

    def post(self, request, format=None):
        serializer = UserLogin_Serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get("email")
            password = serializer.data.get("password")
            try:
                user = authenticate(email=email, password=password)
                if user is None:
                    return Response(
                        {"msg": "Invalid email or password."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                if user.role in ("A", "C") or user.is_verified == True:
                    token = user_generate_token(user)
                    return Response(
                        {
                            "token": token,
                            "user_role": user.role,
                            "msg": "Login Sucessfully",
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {
                            "msg": (
                                "Your account is currently under review as part of our vendor verification process. "
                                "We appreciate your patience and will notify you once your account has been approved. "
                                "Thank you for choosing to partner with us."
                            )
                        },
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
            except Exception as e:
                return Response(
                    {"msg": f"An unexpected error occurred: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


########################################################################################


# this is the class to verify the vendor in the admin site.
class VendorVerifiedView(APIView):
    renderer_classes = [UserRenderer]

    def put(self, request, pk):
        return self.update(request, pk, partial=False)

    def patch(self, request, pk):
        return self.update(request, pk, partial=True)

    def update(self, request, pk, partial):
        try:
            user = get_object_or_404(customeuser, user_id=pk)
            old_verified = user.is_verified
            new_verified = request.data.get("is_verified")
            serializer = CustomeUser_Serializer(
                user, data=request.data, partial=partial
            )
            if serializer.is_valid():
                with transaction.atomic():
                    serializer.save()
                    # checking if the is_verified value is changed or not
                    if (
                        new_verified is not None
                        and str(new_verified).lower() in ["true", "1"]
                        and old_verified != True
                    ):
                        Util.send_verification_email(user)
                    return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"msg": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


########################################################################################


# this is the class to get all the user for the admin.
class UserListView(APIView):
    renderer_classes = [UserRenderer]

    def get(self, request, format=None):
        role = request.query_params.get("role")
        verified = request.query_params.get("is_verified")
        try:
            users = customeuser.objects.all()
            if role:
                users = users.filter(role=role)

            if verified is not None:
                if verified.lower() in ["true", "1"]:
                    users = users.filter(is_verified=True)
                elif verified.lower() in ["false", "0"]:
                    users = users.filter(is_verified=False)
            serializer = CustomeUser_Serializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"msg": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


#########################################################################################


# this is the class for View single user by ID.
class SingleUserView(generics.RetrieveAPIView):
    renderer_classes = [UserRenderer]
    serializer_class = CustomeUserDetail_Serializer

    def get_object(self):
        user_id = self.kwargs.get("pk")
        print(user_id)
        if not user_id:
            raise Http404("User ID not provided")
        return get_object_or_404(customeuser, user_id=user_id)


#########################################################################################


# this is the class for the vendorprofile create.
class VendorProfileView(APIView):
    renderer_classes = [UserRenderer]

    def post(self, request, pk, format=None):
        user = get_object_or_404(customeuser, user_id=pk)
        serializer = VendorProfile_Serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save(user=user)
                return Response(
                    {"msg": "Your vendor profile has been successfully created."},
                    status=status.HTTP_201_CREATED,
                )
            except IntegrityError:
                return Response(
                    {"msg": "A vendor profile already exists for this user."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#########################################################################################


# this is the class for the user delete.
class UserDeleteView(generics.DestroyAPIView):
    renderer_classes = [UserRenderer]
    serializer_class = CustomeUser_Serializer
    queryset = customeuser.objects.all()
    permission_classes = [permissions.IsAdminUser]


#########################################################################################


# this is the class for the login user detal for the profile.
class LoginUserProfileView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        try:
            serializer = CustomeUserDetail_Serializer(request.user)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


#########################################################################################


# this is the class for the profile update for the user.
class ProfileUpdateView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        return self.update_data(request, pk, partial=False)

    def patch(self, request, pk):
        return self.update_data(request, pk, partial=True)

    def update_data(self, request, pk, partial):
        try:
            user_data = get_object_or_404(customeuser, user_id=pk)
            # dynamically extract the model field value.
            user_fields = CustomeUser_Serializer.Meta.fields
            user_data_dict = {k: v for k, v in request.data.items() if k in user_fields}

            # now updating the data if the user is not vendor.
            if user_data.role != "V":
                user_serializer = CustomeUser_Serializer(
                    user_data, data=user_data_dict, partial=partial
                )
                if user_serializer.is_valid(raise_exception=True):
                    user_serializer.save()
                    return Response(
                        {
                            "msg": "User profile updated successfully.",
                            "user": user_serializer.data,
                        },
                        status=status.HTTP_200_OK,
                    )

            # updating the data if the user is vendor.
            vender_user_data = get_object_or_404(VendorProfile, user=user_data.user_id)
            vendor_fields = VendorProfile_Serializer.Meta.fields
            vendor_data_dict = {
                k: v for k, v in request.data.items() if k in vendor_fields
            }
            user_serializer = CustomeUser_Serializer(
                user_data, data=user_data_dict, partial=partial
            )
            vendor_serializer = VendorProfile_Serializer(
                vender_user_data, data=vendor_data_dict, partial=partial
            )

            # now saving the data if both the method is correct.
            if user_serializer.is_valid(
                raise_exception=True
            ) and vendor_serializer.is_valid(raise_exception=True):
                user_serializer.save()
                vendor_serializer.save()
                return Response(
                    {
                        "msg": "Vendor profile updated successfully.",
                        "user": user_serializer.data,
                        "vendor": vendor_serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


#########################################################################################


# this is the class for the user password chage where the user know their real password.
class UserPasswordChnageView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        serializer = UserPasswordChange_Serializer(
            data=request.data, context={"user": request.user}
        )
        if serializer.is_valid(raise_exception=True):
            return Response(
                {"msg": "Your password has been updated successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


#########################################################################################


# this is the class for sending the mail to the user to change the password.
class LinkSendingUserView(APIView):
    throttle_classes = [ForgotPasswordRateThrottle]
    renderer_classes = [UserRenderer]

    def post(self, request, format=None):
        serializer = LinkSendingUser_Serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            return Response(
                {"msg": "Passwoed Reset link send. Please check your Email"},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#########################################################################################


# this is the class for the password reset through the mail.
class UserPasswordChangeMailView(APIView):
    renderer_classes = [UserRenderer]

    def post(self, request, uid, token, format=None):
        serializer = UserPasswordChangeMail_serializer(
            data=request.data, context={"uid": uid, "token": token}
        )
        if serializer.is_valid(raise_exception=True):
            return Response({"msg": "Password Reset Sucessfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
