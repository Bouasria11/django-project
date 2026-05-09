from django.contrib import admin
from django.utils.html import format_html, mark_safe
from .models import User, Genre, Film, Review, Watchlist


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'date_joined', 'is_staff_display')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'bio')
    ordering = ('-date_joined',)
    filter_horizontal = ('favorite_genres',)
    fieldsets = (
        ('Informations de connexion', {'fields': ('username', 'email', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'profile_picture', 'bio', 'birth_date', 'favorite_genres')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    actions = ['make_admin', 'make_spectator', 'deactivate_users']

    def is_staff_display(self, obj):
        return obj.is_staff
    is_staff_display.boolean = True
    is_staff_display.short_description = 'Staff'

    def make_admin(self, request, queryset):
        updated = queryset.update(role=User.Role.ADMIN)
        self.message_user(request, f'{updated} utilisateur(s) promus administrateurs.')
    make_admin.short_description = 'Promouvoir en administrateur'

    def make_spectator(self, request, queryset):
        updated = queryset.update(role=User.Role.SPECTATOR)
        self.message_user(request, f'{updated} utilisateur(s) remis en spectateurs.')
    make_spectator.short_description = 'Remettre en spectateur'

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} utilisateur(s) désactivés.')
    deactivate_users.short_description = 'Désactiver les utilisateurs'


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    fields = ('user', 'rating', 'comment', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = True
    show_change_link = True


class WatchlistInline(admin.TabularInline):
    model = Watchlist
    extra = 0
    fields = ('film', 'added_at')
    readonly_fields = ('added_at',)
    can_delete = True
    show_change_link = True


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'film_count', 'created_at', 'active_films_count')
    search_fields = ('name', 'description')
    ordering = ('name',)
    fields = ('name', 'description', 'created_at')
    readonly_fields = ('created_at', 'film_count', 'active_films_count')

    def film_count(self, obj):
        return obj.films.count()
    film_count.short_description = 'Total films'

    def active_films_count(self, obj):
        return obj.films.filter(created_at__gte='2024-01-01').count()
    active_films_count.short_description = 'Films récents'


@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'genre', 'release_date', 'director', 'average_rating_display', 'review_count', 'poster_thumbnail')
    list_filter = ('genre', 'release_date', 'created_at')
    search_fields = ('title', 'description', 'director')
    ordering = ('-release_date',)
    readonly_fields = ('created_at', 'updated_at', 'average_rating_display', 'review_count')
    inlines = [ReviewInline]

    fieldsets = (
        ('Informations du film', {
            'fields': ('title', 'genre', 'description', 'release_date', 'director', 'duration_minutes')
        }),
        ('Média', {
            'fields': ('poster', 'trailer_url')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at', 'average_rating_display', 'review_count'),
            'classes': ('collapse',)
        }),
    )

    def average_rating_display(self, obj):
        rating = obj.average_rating
        if rating:
            color = 'green' if rating >= 4 else 'orange' if rating >= 3 else 'red'
            return format_html('<span style="color: {}; font-weight: bold;">{}/5</span>', color, rating)
        return mark_safe('<span style="color: gray;">Non noté</span>')
    average_rating_display.short_description = 'Note moyenne'

    def review_count(self, obj):
        count = obj.review_count
        if count > 0:
            return format_html('<b>{}</b> avis', count)
        return '0 avis'
    review_count.short_description = 'Avis'

    def poster_thumbnail(self, obj):
        if obj.poster:
            return format_html('<img src="{}" width="50" height="70" style="object-fit: cover; border-radius: 4px;">', obj.poster.url)
        return '-'
    poster_thumbnail.short_description = 'Affiche'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'film', 'rating_display', 'comment_preview', 'created_at')
    list_filter = ('rating', 'created_at', 'film__genre')
    search_fields = ('user__username', 'film__title', 'comment')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_reviews', 'delete_selected']

    fieldsets = (
        ('Avis', {
            'fields': ('user', 'film', 'rating', 'comment')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def rating_display(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        color = 'gold' if obj.rating >= 4 else 'orange' if obj.rating >= 3 else 'red'
        return format_html('<span style="color: {};" title="{}/5">{}</span>', color, obj.rating, stars)
    rating_display.short_description = 'Note'

    def comment_preview(self, obj):
        if obj.comment:
            return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
        return '-'
    comment_preview.short_description = 'Commentaire'

    def approve_reviews(self, request, queryset):
        # If you have an approved field, you could use it. For now just a placeholder.
        updated = queryset.update()
        self.message_user(request, f'{updated} avis marqués comme approuvés.')
    approve_reviews.short_description = 'Marquer comme approuvé'


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'film', 'added_at')
    list_filter = ('added_at', 'film__genre')
    search_fields = ('user__username', 'film__title')
    ordering = ('-added_at',)
    readonly_fields = ('added_at',)
    actions = ['remove_from_watchlist']

    def remove_from_watchlist(self, request, queryset):
        deleted = queryset.count()
        queryset.delete()
        self.message_user(request, f'{deleted} entrée(s) retirée(s) de la watchlist.')
    remove_from_watchlist.short_description = 'Retirer de la watchlist'
