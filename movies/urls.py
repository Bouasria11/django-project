from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    path('', views.home, name='home'),
    path('films/', views.film_list, name='film_list'),
    path('film/<int:pk>/', views.film_detail, name='film_detail'),
    path('film/ajouter/', views.film_create, name='film_create'),
    path('film/modifier/<int:pk>/', views.film_update, name='film_update'),
    path('film/supprimer/<int:pk>/', views.film_delete, name='film_delete'),
    path('recherche/', views.search_films, name='search_films'),
    path('film/<int:pk>/avis/', views.add_review, name='add_review'),
    path('film/<int:pk>/avis/supprimer/<int:review_id>/', views.delete_review, name='delete_review'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('mon-compte/', views.user_dashboard, name='user_dashboard'),
    path('inscription/', views.register, name='register'),
    path('connexion/', views.login_view, name='login'),
    path('deconnexion/', views.logout_view, name='logout'),
    path('film/<int:pk>/watchlist/', views.toggle_watchlist, name='toggle_watchlist'),
]
