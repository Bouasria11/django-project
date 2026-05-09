"""
API URL routing for the movies application.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

# Create a router and register our ViewSets
router = DefaultRouter()
router.register(r'genres', api_views.GenreViewSet, basename='genre')
router.register(r'films', api_views.FilmViewSet, basename='film')
router.register(r'reviews', api_views.ReviewViewSet, basename='review')
router.register(r'watchlist', api_views.WatchlistViewSet, basename='watchlist')
router.register(r'users', api_views.UserViewSet, basename='user')
router.register(r'stats', api_views.ReviewStatsViewSet, basename='stats')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Additional custom endpoints could be added here if needed
    # Example: path('recommendations/', api_views.RecommendationsView.as_view(), name='recommendations'),
]
