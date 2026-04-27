"""
Classes de permissions personnalisees pour l'API movies.
Gere les acces par role et les permissions au niveau des objets.
"""

from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Autorise la lecture pour tous, mais reserve l'ecriture aux admins.
    """
    def has_permission(self, request, view):
        # Les methodes de lecture sont accessibles sans restriction.
        if request.method in permissions.SAFE_METHODS:
            return True
        # Les methodes d'ecriture necessitent le role administrateur.
        return request.user.is_authenticated and request.user.is_admin_role


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission objet: seul le proprietaire peut modifier l'objet.
    Suppose que l'instance possede un attribut `user`.
    """
    def has_object_permission(self, request, view, obj):
        # La lecture reste autorisee.
        if request.method in permissions.SAFE_METHODS:
            return True
        # L'ecriture exige que l'utilisateur soit proprietaire.
        return obj.user == request.user


class IsAdminOrOwner(permissions.BasePermission):
    """
    Autorise les admins partout, ou les utilisateurs sur leurs propres ressources.
    """
    def has_object_permission(self, request, view, obj):
        # Les administrateurs ont un acces complet.
        if request.user.is_admin_role:
            return True
        # Les autres utilisateurs ne peuvent acceder qu'a leurs ressources.
        return obj.user == request.user


class IsAdminOrFavoritedByUser(permissions.BasePermission):
    """
    Pour Genre: les admins modifient, les autres utilisateurs lisent seulement.
    Les genres sont des ressources globales, sans proprietaire utilisateur.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_admin_role


class CanAddReview(permissions.BasePermission):
    """
    Autorise les utilisateurs connectes a ajouter et gerer leurs avis.
    """
    def has_permission(self, request, view):
        # Tout utilisateur authentifie peut ajouter un avis.
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # La lecture est autorisee.
        if request.method in permissions.SAFE_METHODS:
            return True
        # L'ecriture exige le proprietaire de l'avis ou un administrateur.
        return obj.user == request.user or request.user.is_admin_role


class CanManageWatchlist(permissions.BasePermission):
    """
    Autorise les utilisateurs connectes a gerer leur propre watchlist.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Un utilisateur ne modifie que les entrees de sa propre watchlist.
        return obj.user == request.user
