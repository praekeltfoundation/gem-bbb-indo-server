
from rest_framework.permissions import BasePermission


class IsAdminOrOwner(BasePermission):

    def has_permission(self, request, view):
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        print("Checking permissions Request %s == Object %s" % (request.user, obj.user))
        return request.user.is_staff or obj.user == request.user
