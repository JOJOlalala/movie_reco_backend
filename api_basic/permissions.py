from rest_framework.permissions import BasePermission


class IsAdminOrIsSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        currentUser = request.user
        if currentUser and currentUser.is_authenticated:
            return currentUser.is_staff or currentUser.username == obj.username
        return False
