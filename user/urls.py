from django.urls import path
from user import views

urlpatterns = [
    path(
        "user/registration/",
        views.UserRegistrationView.as_view(),
        name="path to register the user in the application",
    ),
    path(
        "user/login/",
        views.UserLoginView.as_view(),
        name="path to login user",
    ),
    path(
        "vendor/verified/<uuid:pk>/",
        views.VendorVerifiedView.as_view(),
        name="path to verified the vendor",
    ),
    path(
        "user/list/",
        views.UserListView.as_view(),
        name="path to get the user list based on filtering",
    ),
    path(
        "single/user-view/<uuid:pk>/",
        views.SingleUserView.as_view(),
        name="path to get the detail of the single user from uer id.",
    ),
    path(
        "user/delete/<uuid:pk>/",
        views.UserDeleteView.as_view(),
        name="path to delete the user from the website",
    ),
    path(
        "login/user/profile/",
        views.LoginUserProfileView.as_view(),
        name="path to get the login user profile",
    ),
    path(
        "vendor/profil/<uuid:pk>/",
        views.VendorProfileView.as_view(),
        name="path to create the vendro profile",
    ),
    path(
        "user/profile/update/<uuid:pk>/",
        views.ProfileUpdateView.as_view(),
        name="path to update the prfile of the user",
    ),
    path(
        "user/password-change/",
        views.UserPasswordChnageView.as_view(),
        name="path to change the password of the users old password known",
    ),
    path(
        "password/reset/link/",
        views.LinkSendingUserView.as_view(),
        name="path to send the reset link to the user",
    ),
    path(
        "user/password/reset-mail/<uid>/<token>/",
        views.UserPasswordChangeMailView.as_view(),
        name="path to reset the password through the mail",
    ),
    ##############################################################################################
    path("", views.home_view),
]
