from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Film, Genre, Review, User, Watchlist
from .forms import (
    FilmForm, GenreForm, ReviewForm, UserRegistrationForm,
    UserLoginForm, UserProfileForm
)
from datetime import datetime, timedelta

def home(request):
    """Page d'accueil avec les films recents et les mieux notes."""
    recent_films = Film.objects.all().order_by('-created_at')[:8]
    top_rated_films = Film.objects.annotate(
        avg_rating=Avg('reviews__rating')
    ).filter(avg_rating__isnull=False).order_by('-avg_rating')[:8]

    context = {
        'recent_films': recent_films,
        'top_rated_films': top_rated_films,
    }
    return render(request, 'movies/home.html', context)

def film_list(request):
    """Liste les films avec pagination et filtres simples."""
    genre_id = request.GET.get('genre')
    sort_by = request.GET.get('sort', '-release_date')
    films = Film.objects.all()

    if genre_id:
        # Filtre facultatif par genre depuis les parametres de l'URL.
        films = films.filter(genre_id=genre_id)

    if sort_by:
        films = films.order_by(sort_by)

    paginator = Paginator(films, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    genres = Genre.objects.all().order_by('name')
    context = {
        'page_obj': page_obj,
        'genres': genres,
        'selected_genre': genre_id,
        'sort_by': sort_by,
    }
    return render(request, 'movies/film_list.html', context)

def film_detail(request, pk):
    """Affiche le detail d'un film avec ses avis."""
    film = get_object_or_404(Film, pk=pk)
    reviews = film.reviews.all()
    user_review = None
    is_in_watchlist = False

    if request.user.is_authenticated:
        # Recupere l'avis et la watchlist uniquement pour les utilisateurs connectes.
        user_review = reviews.filter(user=request.user).first()
        is_in_watchlist = Watchlist.objects.filter(user=request.user, film=film).exists()

    # Calcule la repartition des notes pour l'affichage detaille.
    rating_counts = reviews.values('rating').annotate(count=Count('rating')).order_by('rating')

    context = {
        'film': film,
        'reviews': reviews,
        'user_review': user_review,
        'is_in_watchlist': is_in_watchlist,
        'rating_counts': rating_counts,
        'average_rating': film.average_rating,
    }
    return render(request, 'movies/film_detail.html', context)

@login_required
def film_create(request):
    """Cree un nouveau film, reserve aux administrateurs."""
    if not request.user.is_admin_role:
        messages.error(request, "Accès refusé. Droits d'administrateur requis.")
        return redirect('movies:home')

    if request.method == 'POST':
        form = FilmForm(request.POST, request.FILES)
        if form.is_valid():
            film = form.save()
            messages.success(request, f'Le film "{film.title}" a été créé avec succès.')
            return redirect('movies:film_detail', pk=film.pk)
    else:
        form = FilmForm()

    context = {'form': form, 'title': 'Ajouter un film'}
    return render(request, 'movies/film_form.html', context)

@login_required
def film_update(request, pk):
    """Modifie un film existant, reserve aux administrateurs."""
    if not request.user.is_admin_role:
        messages.error(request, "Accès refusé. Droits d'administrateur requis.")
        return redirect('movies:home')

    film = get_object_or_404(Film, pk=pk)
    if request.method == 'POST':
        form = FilmForm(request.POST, request.FILES, instance=film)
        if form.is_valid():
            film = form.save()
            messages.success(request, f'Le film "{film.title}" a été mis à jour.')
            return redirect('movies:film_detail', pk=film.pk)
    else:
        form = FilmForm(instance=film)

    context = {'form': form, 'title': 'Modifier le film', 'film': film}
    return render(request, 'movies/film_form.html', context)

@login_required
def film_delete(request, pk):
    """Supprime un film, reserve aux administrateurs."""
    if not request.user.is_admin_role:
        messages.error(request, "Accès refusé. Droits d'administrateur requis.")
        return redirect('movies:home')

    film = get_object_or_404(Film, pk=pk)
    if request.method == 'POST':
        film_title = film.title
        film.delete()
        messages.success(request, f'Le film "{film_title}" a été supprimé.')
        return redirect('movies:film_list')

    context = {'film': film}
    return render(request, 'movies/film_confirm_delete.html', context)

def search_films(request):
    """Recherche des films par texte, genre ou annee."""
    query = request.GET.get('q', '')
    genre_id = request.GET.get('genre')
    year = request.GET.get('year')
    films = Film.objects.all()

    if query:
        films = films.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(director__icontains=query)
        )

    if genre_id:
        films = films.filter(genre_id=genre_id)

    if year:
        films = films.filter(release_date__year=year)

    sort_by = request.GET.get('sort', '-release_date')
    if sort_by:
        films = films.order_by(sort_by)

    paginator = Paginator(films, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Liste des annees disponibles pour alimenter le filtre.
    years = Film.objects.dates('release_date', 'year', order='DESC')

    # Objet genre selectionne, utile pour l'affichage du libelle.
    selected_genre_obj = None
    if genre_id:
        selected_genre_obj = Genre.objects.filter(id=genre_id).first()

    context = {
        'page_obj': page_obj,
        'query': query,
        'genres': Genre.objects.all().order_by('name'),
        'selected_genre': genre_id,
        'selected_genre_obj': selected_genre_obj,
        'years': years,
        'selected_year': year,
        'sort_by': sort_by,
        'total_results': films.count(),
    }
    return render(request, 'movies/search.html', context)

@login_required
def add_review(request, pk):
    """Ajoute ou met a jour l'avis de l'utilisateur sur un film."""
    film = get_object_or_404(Film, pk=pk)
    existing_review = Review.objects.filter(user=request.user, film=film).first()

    if request.method == 'POST':
        # Reutilise l'avis existant pour empecher les doublons utilisateur/film.
        if existing_review:
            form = ReviewForm(request.POST, instance=existing_review)
        else:
            form = ReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.film = film
            review.save()
            action = 'modifié' if existing_review else 'ajouté'
            messages.success(request, f'Avis {action} avec succès.')
            return redirect('movies:film_detail', pk=film.pk)
    else:
        if existing_review:
            form = ReviewForm(instance=existing_review)
        else:
            form = ReviewForm()

    context = {'form': form, 'film': film, 'is_edit': existing_review is not None}
    return render(request, 'movies/review_form.html', context)

@login_required
def delete_review(request, pk, review_id):
    """Supprime un avis appartenant a l'utilisateur connecte."""
    review = get_object_or_404(Review, pk=review_id, user=request.user)
    film_pk = review.film.pk
    review.delete()
    messages.success(request, 'Avis supprimé avec succès.')
    return redirect('movies:film_detail', pk=film_pk)

@login_required
def recommendations(request):
    """Recommandations personnalisees selon les notes de l'utilisateur."""
    user_reviews = Review.objects.filter(user=request.user).select_related('film', 'film__genre')

    if not user_reviews.exists():
        messages.info(request, "Notez des films pour obtenir des recommandations personnalisées.")
        return redirect('movies:film_list')

    # Identifie les genres preferes a partir des notes elevees.
    liked_genres = {}
    for review in user_reviews.filter(rating__gte=4):
        genre = review.film.genre
        if genre:
            liked_genres[genre.id] = liked_genres.get(genre.id, 0) + 1

    # Propose des films des genres preferes que l'utilisateur n'a pas encore notes.
    recommended_films = Film.objects.filter(genre__in=liked_genres.keys()).exclude(
        reviews__user=request.user
    ).annotate(
        avg_rating=Avg('reviews__rating'),
        rating_count=Count('reviews')
    ).filter(rating_count__gte=1).order_by('-avg_rating')[:12]

    # Repli: films populaires quand les recommandations personnalisees sont limitees.
    popular_films = Film.objects.annotate(
        rating_count=Count('reviews')
    ).filter(rating_count__gte=3).exclude(
        reviews__user=request.user
    ).order_by('-rating_count')[:6]

    context = {
        'recommended_films': recommended_films,
        'popular_films': popular_films,
        'liked_genres': liked_genres,
    }
    return render(request, 'movies/recommendations.html', context)

@login_required
def user_dashboard(request):
    """Tableau de bord avec profil, watchlist et historique des avis."""
    user_reviews = Review.objects.filter(user=request.user).select_related('film').order_by('-created_at')[:10]
    watchlist = Watchlist.objects.filter(user=request.user).select_related('film').order_by('-added_at')[:10]

    # Statistiques personnelles de l'utilisateur connecte.
    total_reviews = Review.objects.filter(user=request.user).count()
    total_ratings_given = Review.objects.filter(user=request.user).aggregate(Sum('rating'))['rating__sum'] or 0
    avg_rating_given = Review.objects.filter(user=request.user).aggregate(Avg('rating'))['rating__avg'] or 0

    context = {
        'user_reviews': user_reviews,
        'watchlist': watchlist,
        'total_reviews': total_reviews,
        'total_ratings_given': total_ratings_given,
        'avg_rating_given': round(avg_rating_given, 1),
    }
    return render(request, 'movies/dashboard.html', context)

def register(request):
    """Inscription d'un nouvel utilisateur."""
    if request.user.is_authenticated:
        return redirect('movies:home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Bienvenue, {user.username}!')
            return redirect('movies:home')
    else:
        form = UserRegistrationForm()

    context = {'form': form, 'title': 'Inscription'}
    return render(request, 'movies/register.html', context)

def login_view(request):
    """Connexion d'un utilisateur."""
    if request.user.is_authenticated:
        return redirect('movies:home')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Connecté en tant que {username}')
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
    else:
        form = UserLoginForm()

    context = {'form': form, 'title': 'Connexion'}
    return render(request, 'movies/login.html', context)

@login_required
def logout_view(request):
    """Deconnexion de l'utilisateur."""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté.')
    return redirect('movies:home')

@login_required
def toggle_watchlist(request, pk):
    """Ajoute ou retire un film de la watchlist de l'utilisateur."""
    film = get_object_or_404(Film, pk=pk)
    watchlist_item, created = Watchlist.objects.get_or_create(user=request.user, film=film)

    if not created:
        watchlist_item.delete()
        messages.info(request, f'"{film.title}" retiré de la liste de surveillance.')
    else:
        messages.success(request, f'"{film.title}" ajouté à la liste de surveillance.')

    return redirect('movies:film_detail', pk=film.pk)
