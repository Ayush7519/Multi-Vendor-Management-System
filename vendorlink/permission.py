from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


class IsVendorUser(BasePermission):

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            raise PermissionDenied(
                detail="Authentication credentials were not provided."
            )

        if user.is_verified:
            return True

        raise PermissionDenied(
            detail="You must be a verified vendor to access this resource."
        )
