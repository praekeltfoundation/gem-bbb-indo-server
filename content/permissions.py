
from rest_framework.permissions import BasePermission


class IsUserSelf(BasePermission):

    def has_object_permission(self, request, view, obj):
        return request.user == obj


class IsAdminOrOwner(BasePermission):

    def has_permission(self, request, view):
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user
