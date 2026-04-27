from django.db import models
from django.contrib.auth.models import AbstractUser, Permission
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Modele utilisateur personnalise avec permissions basees sur le role."""

    class Role(models.TextChoices):
        SPECTATOR = 'SPECTATOR', _('Spectateur')
        ADMIN = 'ADMIN', _('Administrateur')

    base_role = Role.SPECTATOR

    role = models.CharField(
        max_length=50,
        choices=Role.choices,
        default=Role.SPECTATOR,
    )

    profile_picture = models.ImageField(
        upload_to='profiles/',
        null=True,
        blank=True,
        default='profiles/default.jpg'
    )
    bio = models.TextField(max_length=500, blank=True)
    favorite_genres = models.ManyToManyField('Genre', blank=True, related_name='favorited_by')
    birth_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Synchronise le role metier avec les permissions natives de Django.
        if self.role == self.Role.ADMIN:
            self.is_staff = True
            self.is_superuser = True
        else:
            self.is_staff = False
            self.is_superuser = False
        super().save(*args, **kwargs)

    @property
    def is_spectator(self):
        return self.role == self.Role.SPECTATOR

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class Genre(models.Model):
    """Modele representant un genre de film."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Genre'
        verbose_name_plural = 'Genres'

    def __str__(self):
        return self.name

class Film(models.Model):
    """Modele principal du catalogue de films."""

    title = models.CharField(max_length=200)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, related_name='films')
    description = models.TextField(max_length=2000)
    release_date = models.DateField()
    director = models.CharField(max_length=200, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    poster = models.ImageField(upload_to='posters/', null=True, blank=True)
    trailer_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Les index accelerent les recherches et tris les plus frequents.
        ordering = ['-release_date', 'title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['release_date']),
            models.Index(fields=['genre']),
        ]

    def __str__(self):
        return self.title

    @property
    def average_rating(self):
        # Calcule la moyenne des notes a partir des avis lies au film.
        reviews = self.reviews.all()
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return None

    @property
    def review_count(self):
        # Nombre total d'avis associes au film.
        return self.reviews.count()

class Review(models.Model):
    """Avis et note laisses par un utilisateur sur un film."""

    RATING_CHOICES = [
        (1, '1 - Mauvais'),
        (2, '2 - Pauvre'),
        (3, '3 - Correct'),
        (4, '4 - Bon'),
        (5, '5 - Excellent'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    film = models.ForeignKey(Film, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(max_length=2000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Un utilisateur ne peut laisser qu'un seul avis par film.
        unique_together = ['user', 'film']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['film', '-created_at']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.film.title} ({self.rating}/5)"

    def clean(self):
        # Validation de securite cote modele, en plus des formulaires/API.
        from django.core.exceptions import ValidationError
        if self.rating < 1 or self.rating > 5:
            raise ValidationError({'rating': 'La note doit être comprise entre 1 et 5.'})

class Watchlist(models.Model):
    """Liste personnelle de films a regarder."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    film = models.ForeignKey(Film, on_delete=models.CASCADE, related_name='in_watchlists')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Evite les doublons dans la watchlist d'un meme utilisateur.
        unique_together = ['user', 'film']
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} - {self.film.title}"
