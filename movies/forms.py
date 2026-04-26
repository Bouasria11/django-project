from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User, Film, Review, Genre

class GenreForm(forms.ModelForm):
    # Formulaire simple pour creer ou modifier un genre.
    class Meta:
        model = Genre
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class FilmForm(forms.ModelForm):
    # Formulaire principal de gestion des films dans l'interface web.
    class Meta:
        model = Film
        fields = ['title', 'genre', 'description', 'release_date', 'director', 'duration_minutes', 'poster', 'trailer_url']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'genre': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'release_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'director': forms.TextInput(attrs={'class': 'form-control'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'poster': forms.FileInput(attrs={'class': 'form-control'}),
            'trailer_url': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def clean_duration_minutes(self):
        # Refuse une duree nulle ou negative.
        duration = self.cleaned_data.get('duration_minutes')
        if duration is not None and duration <= 0:
            raise ValidationError("La durée doit être positive.")
        return duration

class ReviewForm(forms.ModelForm):
    # Formulaire utilise pour ajouter ou modifier un avis.
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Partagez votre avis sur ce film...'}),
        }

class UserRegistrationForm(UserCreationForm):
    # Etend le formulaire Django pour ajouter email, role et informations de profil.
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(
        choices=User.Role.choices,
        initial=User.Role.SPECTATOR,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role', 'bio', 'profile_picture', 'birth_date']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def save(self, commit=True):
        # Sauvegarde les champs personnalises apres la creation Django de l'utilisateur.
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        role = self.cleaned_data.get('role')
        if role:
            user.role = role
        if commit:
            user.save()
        return user

class UserLoginForm(AuthenticationForm):
    # Personnalise les champs de connexion avec les classes Bootstrap.
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom d\'utilisateur'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'}))

class UserProfileForm(forms.ModelForm):
    # Formulaire de mise a jour du profil utilisateur.
    class Meta:
        model = User
        fields = ['username', 'email', 'bio', 'profile_picture', 'birth_date', 'favorite_genres']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'favorite_genres': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
        }

class WatchlistForm(forms.Form):
    # Formulaire minimal pour transmettre l'identifiant du film.
    film = forms.IntegerField(widget=forms.HiddenInput())
