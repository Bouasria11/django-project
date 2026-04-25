"""
Routage des URLs API pour l'application movies.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

# Le routeur genere automatiquement les routes CRUD de chaque ViewSet.
router = DefaultRouter()
router.register(r'genres', api_views.GenreViewSet, basename='genre')
router.register(r'films', api_views.FilmViewSet, basename='film')
router.register(r'reviews', api_views.ReviewViewSet, basename='review')
router.register(r'watchlist', api_views.WatchlistViewSet, basename='watchlist')
router.register(r'users', api_views.UserViewSet, basename='user')
router.register(r'stats', api_views.ReviewStatsViewSet, basename='stats')

urlpatterns = [
    # Toutes les routes API exposees par le routeur DRF.
    path('', include(router.urls)),
    
    # Ajouter ici des endpoints API supplementaires si necessaire.
    # Exemple: path('recommendations/', api_views.RecommendationsView.as_view(), name='recommendations'),
]
