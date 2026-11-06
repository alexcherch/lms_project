from rest_framework import permissions


class IsModer(permissions.BasePermission):
    message = "Вы не являетесь модератором."

    def has_permission(self, request, view):
        return request.user.groups.filter(name="moderators").exists()


class IsOwner(permissions.BasePermission):
    message = "Вы не являетесь владельцем этого объекта."

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        return obj == request.user
