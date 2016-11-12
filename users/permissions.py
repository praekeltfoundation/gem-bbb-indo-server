
from rest_framework.permissions import BasePermission


class IsUserSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj


class IsRegisteringOrSelf(BasePermission):
    """Allows anyone to POST, but only the user can list, retrieve and update themselves."""

    def has_object_permission(self, request, view, obj):
        return request.method == 'POST' or (request.user.is_authenticated() and request.user == obj)
