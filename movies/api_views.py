"""
Vues API et ViewSets pour l'application movies.
Fournit les operations CRUD avec permissions et optimisations adaptees.
"""

from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django.db.models import Count, Avg, Q, Prefetch
from django.shortcuts import get_object_or_404

from .models import User, Genre, Film, Review, Watchlist
from .serializers import (
    UserSerializer, GenreSerializer, FilmSerializer,
    ReviewSerializer, WatchlistSerializer, FilmStatsSerializer,
    UserReviewStatsSerializer
)
from .permissions import (
    IsAdminOrReadOnly, IsOwnerOrReadOnly, IsAdminOrOwner,
    IsAdminOrFavoritedByUser, CanAddReview, CanManageWatchlist
)


class GenreViewSet(viewsets.ModelViewSet):
    """
    Endpoint API pour les genres.
    - Lecture: disponible pour tous
    - Creation/modification/suppression: reservees aux administrateurs
    """
    queryset = Genre.objects.annotate(films_count=Count('films')).all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrFavoritedByUser]
    lookup_field = 'id'
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'films_count']
    ordering = ['name']

    def perform_create(self, serializer):
        serializer.save()


class FilmViewSet(viewsets.ModelViewSet):
    """
    Endpoint API pour les films.
    - Lecture: disponible pour tous
    - Creation/modification/suppression: reservees aux administrateurs
    - Actions personnalisees: stats, toggle_watchlist
    """
    queryset = Film.objects.select_related('genre').all()
    serializer_class = FilmSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'id'
    search_fields = ['title', 'description', 'director']
    ordering_fields = ['title', 'release_date', 'created_at', 'average_rating']
    ordering = ['-release_date', 'title']
    filterset_fields = ['genre']

    def get_queryset(self):
        """Optimise la requete avec les statistiques calculees."""
        queryset = super().get_queryset()
        queryset = queryset.annotate(
            average_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        )
        return queryset

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def stats(self, request, id=None):
        """Retourne les statistiques detaillees d'un film."""
        film = self.get_object()
        serializer = FilmStatsSerializer(film)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_watchlist(self, request, id=None):
        """Ajoute ou retire le film de la watchlist de l'utilisateur."""
        film = self.get_object()
        user = request.user
        watchlist_item, created = Watchlist.objects.get_or_create(user=user, film=film)
        
        if not created:
            watchlist_item.delete()
            return Response({
                'message': 'Removed from watchlist',
                'in_watchlist': False
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'Added to watchlist',
                'in_watchlist': True
            }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def featured(self, request):
        """Retourne les films mis en avant, bien notes et assez commentes."""
        films = Film.objects.annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ).filter(review_count__gte=3).order_by('-avg_rating')[:8]
        
        serializer = self.get_serializer(films, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def recent(self, request):
        """Retourne les films ajoutes recemment."""
        films = Film.objects.order_by('-created_at')[:8]
        serializer = self.get_serializer(films, many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    Endpoint API pour les avis.
    - Les utilisateurs gerent leurs propres avis
    - Les administrateurs ont un acces complet
    - Les utilisateurs connectes peuvent lister et consulter les avis
    """
    queryset = Review.objects.select_related('user', 'film').all()
    serializer_class = ReviewSerializer
    permission_classes = [CanAddReview]
    lookup_field = 'id'
    search_fields = ['comment']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    filterset_fields = ['film', 'user', 'rating']

    def perform_create(self, serializer):
        """Associe automatiquement l'utilisateur courant."""
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """Utilise select_related pour eviter les requetes N+1."""
        return super().get_queryset().select_related('user', 'film')


class WatchlistViewSet(viewsets.ModelViewSet):
    """
    Endpoint API pour les watchlists.
    - Les utilisateurs voient seulement leur propre watchlist
    - Les administrateurs peuvent consulter toutes les watchlists
    """
    queryset = Watchlist.objects.select_related('user', 'film').all()
    serializer_class = WatchlistSerializer
    permission_classes = [CanManageWatchlist]
    lookup_field = 'id'
    ordering_fields = ['added_at']
    ordering = ['-added_at']

    def get_queryset(self):
        """Filtre la watchlist selon le role de l'utilisateur."""
        user = self.request.user
        if user.is_admin_role:
            return super().get_queryset()
        return super().get_queryset().filter(user=user)

    def perform_create(self, serializer):
        """Associe automatiquement l'utilisateur courant."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_watchlist(self, request):
        """Retourne la watchlist de l'utilisateur courant."""
        queryset = self.get_queryset().filter(user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """
    Endpoint API pour les utilisateurs.
    - Les utilisateurs consultent et modifient leur propre profil
    - Les administrateurs ont un acces complet
    """
    queryset = User.objects.prefetch_related('favorite_genres', 'watchlist').all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'username'
    search_fields = ['username', 'email', 'bio']
    ordering_fields = ['username', 'date_joined']
    ordering = ['username']

    def get_queryset(self):
        """Les admins voient tout, les autres voient seulement les profils publics."""
        user = self.request.user
        if user.is_authenticated and user.is_admin_role:
            return super().get_queryset()
        # Les utilisateurs standards ne voient que les informations publiques.
        return super().get_queryset().only('id', 'username', 'bio', 'profile_picture')

    def get_permissions(self):
        """
        Permissions personnalisees:
        - Liste/detail: utilisateur authentifie
        - Creation: inscription publique
        - Modification/suppression: proprietaire ou admin uniquement
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        elif self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminOrOwner]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def reviews(self, request, username=None):
        """Retourne tous les avis d'un utilisateur."""
        user = self.get_object()
        reviews = user.reviews.select_related('film').order_by('-created_at')
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ReviewSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def watchlist(self, request, username=None):
        """Retourne la watchlist d'un utilisateur."""
        user = self.get_object()
        # Seul le proprietaire ou un admin peut consulter cette watchlist.
        if not request.user.is_admin_role and user != request.user:
            return Response(
                {'detail': 'You do not have permission to view this watchlist.'},
                status=status.HTTP_403_FORBIDDEN
            )
        watchlist = user.watchlist.select_related('film').order_by('-added_at')
        serializer = WatchlistSerializer(watchlist, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def stats(self, request, username=None):
        """Retourne les statistiques d'un utilisateur."""
        user = self.get_object()
        serializer = UserReviewStatsSerializer(user)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Cree un utilisateur avec mot de passe hache."""
        user = serializer.save()
        # Point d'extension: envoyer un email de bienvenue ou declencher un signal.


class ReviewStatsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    ViewSet pour les statistiques agregees des avis.
    Fournit les films les mieux notes, les stats par genre, etc.
    """
    queryset = Film.objects.all()
    serializer_class = FilmStatsSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def top_rated(self, request):
        """Retourne les films les mieux notes avec au moins 5 avis."""
        films = Film.objects.annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ).filter(review_count__gte=5).order_by('-avg_rating')[:10]
        serializer = FilmStatsSerializer(films, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def most_reviewed(self, request):
        """Retourne les films les plus commentes."""
        films = Film.objects.annotate(
            review_count=Count('reviews')
        ).order_by('-review_count')[:10]
        serializer = self.get_serializer(films, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def genre_stats(self, request):
        """Retourne les statistiques groupees par genre."""
        from django.db.models import Avg, Count
        genre_stats = Genre.objects.annotate(
            film_count=Count('films'),
            avg_rating=Avg('films__reviews__rating')
        ).values('id', 'name', 'film_count', 'avg_rating')
        return Response(list(genre_stats))
