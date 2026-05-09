"""
API Views and ViewSets for the movies application.
Provides CRUD operations with proper permissions and optimizations.
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
    API endpoint for Film Genres.
    - List/Retrieve: Available to all
    - Create/Update/Delete: Admin only
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
    API endpoint for Films.
    - List/Retrieve: Available to all
    - Create/Update/Delete: Admin only
    - Custom actions: stats, toggle_watchlist
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
        """Optimize queryset with annotations"""
        queryset = super().get_queryset()
        queryset = queryset.annotate(
            average_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        )
        return queryset

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def stats(self, request, id=None):
        """Get detailed statistics for a film"""
        film = self.get_object()
        serializer = FilmStatsSerializer(film)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_watchlist(self, request, id=None):
        """Add or remove film from user's watchlist"""
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
        """Get featured films (top rated with sufficient reviews)"""
        films = Film.objects.annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ).filter(review_count__gte=3).order_by('-avg_rating')[:8]
        
        serializer = self.get_serializer(films, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def recent(self, request):
        """Get recently added films"""
        films = Film.objects.order_by('-created_at')[:8]
        serializer = self.get_serializer(films, many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Film Reviews.
    - Users can create, update, delete their own reviews
    - Admins have full access
    - All authenticated users can list/view reviews
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
        """Auto-assign current user"""
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """Optimize with select_related to avoid N+1 queries"""
        return super().get_queryset().select_related('user', 'film')


class WatchlistViewSet(viewsets.ModelViewSet):
    """
    API endpoint for User Watchlist.
    - Users can only access their own watchlist
    - Admins can view all watchlists
    """
    queryset = Watchlist.objects.select_related('user', 'film').all()
    serializer_class = WatchlistSerializer
    permission_classes = [CanManageWatchlist]
    lookup_field = 'id'
    ordering_fields = ['added_at']
    ordering = ['-added_at']

    def get_queryset(self):
        """Filter to show only user's own watchlist unless admin"""
        user = self.request.user
        if user.is_admin_role:
            return super().get_queryset()
        return super().get_queryset().filter(user=user)

    def perform_create(self, serializer):
        """Auto-assign current user"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_watchlist(self, request):
        """Get current user's watchlist"""
        queryset = self.get_queryset().filter(user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Users.
    - Users can view and edit their own profile
    - Admins have full access
    """
    queryset = User.objects.prefetch_related('favorite_genres', 'watchlist').all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'username'
    search_fields = ['username', 'email', 'bio']
    ordering_fields = ['username', 'date_joined']
    ordering = ['username']

    def get_queryset(self):
        """Admins see all users, regular users see public profiles"""
        user = self.request.user
        if user.is_authenticated and user.is_admin_role:
            return super().get_queryset()
        # Regular users can only see basic info of other users
        return super().get_queryset().only('id', 'username', 'bio', 'profile_picture')

    def get_permissions(self):
        """
        Custom permissions:
        - List/Retrieve: Any authenticated user
        - Create: Allow any (public registration)
        - Update/Delete: Owner or admin only
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
        """Get all reviews by a specific user"""
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
        """Get user's watchlist"""
        user = self.get_object()
        # Users can only see their own watchlist unless they're admin
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
        """Get user statistics"""
        user = self.get_object()
        serializer = UserReviewStatsSerializer(user)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Create user with hashed password"""
        user = serializer.save()
        # Optionally send welcome email or other signals


class ReviewStatsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    ViewSet for aggregated review statistics.
    Provides top-rated films, genre stats, etc.
    """
    queryset = Film.objects.all()
    serializer_class = FilmStatsSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def top_rated(self, request):
        """Get top-rated films (min 5 reviews)"""
        films = Film.objects.annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ).filter(review_count__gte=5).order_by('-avg_rating')[:10]
        serializer = FilmStatsSerializer(films, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def most_reviewed(self, request):
        """Get most reviewed films"""
        films = Film.objects.annotate(
            review_count=Count('reviews')
        ).order_by('-review_count')[:10]
        serializer = self.get_serializer(films, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def genre_stats(self, request):
        """Get statistics by genre"""
        from django.db.models import Avg, Count
        genre_stats = Genre.objects.annotate(
            film_count=Count('films'),
            avg_rating=Avg('films__reviews__rating')
        ).values('id', 'name', 'film_count', 'avg_rating')
        return Response(list(genre_stats))
