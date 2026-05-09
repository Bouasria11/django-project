"""
Custom permission classes for the movies API.
Provides role-based access control and object-level permissions.
"""

from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allow read access to all, but only admins can create, update, or delete.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions require admin role
        return request.user.is_authenticated and request.user.is_admin_role


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `user` attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions require the user to be the owner
        return obj.user == request.user


class IsAdminOrOwner(permissions.BasePermission):
    """
    Allow admins full access, or users to access their own resources.
    """
    def has_object_permission(self, request, view, obj):
        # Admins have full access
        if request.user.is_admin_role:
            return True
        # Users can only access their own resources
        return obj.user == request.user


class IsAdminOrFavoritedByUser(permissions.BasePermission):
    """
    For Genre: admins can edit, users can only read.
    Genres are global resources, not user-owned.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_admin_role


class CanAddReview(permissions.BasePermission):
    """
    Allows authenticated users to add reviews, but only edit their own.
    """
    def has_permission(self, request, view):
        # Any authenticated user can add a review
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read permissions allowed
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions require the user to be the review owner or admin
        return obj.user == request.user or request.user.is_admin_role


class CanManageWatchlist(permissions.BasePermission):
    """
    Allows authenticated users to manage their own watchlist.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Users can only modify their own watchlist items
        return obj.user == request.user
