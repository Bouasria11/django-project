"""
Serializers for the movies API.
Handles validation, transformation, and representation of model instances.
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, Genre, Film, Review, Watchlist


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with role-based field handling"""
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    email = serializers.EmailField(required=True)
    role = serializers.ChoiceField(choices=User.Role.choices, required=False)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    favorite_genres = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Genre.objects.all(), required=False
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'role',
            'profile_picture', 'bio', 'birth_date', 'favorite_genres',
            'is_staff', 'is_superuser', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'is_staff', 'is_superuser', 'date_joined', 'last_login']

    def validate_username(self, value):
        """Validate username uniqueness"""
        if self.instance:
            # Update scenario
            if User.objects.filter(username=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("This username is already taken.")
        else:
            # Create scenario
            if User.objects.filter(username=value).exists():
                raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        """Validate email uniqueness and format"""
        if self.instance:
            if User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("This email is already in use.")
        else:
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("This email is already in use.")
        return value

    def validate_password(self, value):
        """Use Django's built-in password validation"""
        try:
            validate_password(value, self.instance)
        except ValidationError as e:
            raise serializers.ValidationError(str(e.messages[0]))
        return value

    def validate_role(self, value):
        """Only admins can assign admin role"""
        request = self.context.get('request')
        if value == User.Role.ADMIN:
            if not request or not request.user.is_admin_role:
                raise serializers.ValidationError("Only admins can assign admin role.")
        return value

    def create(self, validated_data):
        """Create user with hashed password"""
        password = validated_data.pop('password', None)
        favorite_genres = validated_data.pop('favorite_genres', [])
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        user.favorite_genres.set(favorite_genres)
        return user

    def update(self, instance, validated_data):
        """Update user with proper password handling"""
        password = validated_data.pop('password', None)
        favorite_genres = validated_data.pop('favorite_genres', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        
        if favorite_genres is not None:
            instance.favorite_genres.set(favorite_genres)
        
        return instance


class GenreSerializer(serializers.ModelSerializer):
    """Serializer for Genre model"""
    films_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Genre
        fields = ['id', 'name', 'description', 'films_count', 'created_at']
        read_only_fields = ['id', 'created_at', 'films_count']

    def validate_name(self, value):
        """Validate genre name uniqueness"""
        if self.instance:
            if Genre.objects.filter(name__iexact=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("A genre with this name already exists.")
        else:
            if Genre.objects.filter(name__iexact=value).exists():
                raise serializers.ValidationError("A genre with this name already exists.")
        return value


class FilmSerializer(serializers.ModelSerializer):
    """Serializer for Film model with computed fields"""
    genre = GenreSerializer(read_only=True)
    genre_id = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        write_only=True,
        source='genre',
        required=False,
        allow_null=True
    )
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    is_in_watchlist = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Film
        fields = [
            'id', 'title', 'genre', 'genre_id', 'description',
            'release_date', 'director', 'duration_minutes',
            'poster', 'trailer_url', 'average_rating', 'review_count',
            'is_in_watchlist', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'average_rating', 'review_count', 'is_in_watchlist']

    def get_is_in_watchlist(self, obj):
        """Check if film is in current user's watchlist"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.in_watchlists.filter(user=request.user).exists()
        return False

    def validate_duration_minutes(self, value):
        """Validate duration is positive"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Duration must be positive.")
        return value

    def validate_release_date(self, value):
        """Validate release date is not in the future (optional business rule)"""
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("Release date cannot be in the future.")
        return value


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model with ownership info"""
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source='user',
        required=False
    )
    film_id = serializers.PrimaryKeyRelatedField(
        queryset=Film.objects.all(),
        write_only=True,
        source='film'
    )
    film_title = serializers.CharField(source='film.title', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'user_id', 'film_id', 'film_title',
            'rating', 'comment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate_rating(self, value):
        """Ensure rating is between 1 and 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, attrs):
        """
        Validate that a user can only have one review per film.
        """
        user = attrs.get('user') or self.context['request'].user
        film = attrs.get('film')

        if self.instance:
            # Update scenario: exclude current instance
            if Review.objects.filter(user=user, film=film).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("You have already reviewed this film.")
        else:
            # Create scenario
            if Review.objects.filter(user=user, film=film).exists():
                raise serializers.ValidationError("You have already reviewed this film.")
        
        return attrs

    def create(self, validated_data):
        """Auto-assign current user if not provided"""
        request = self.context.get('request')
        if not validated_data.get('user'):
            validated_data['user'] = request.user
        return super().create(validated_data)


class WatchlistSerializer(serializers.ModelSerializer):
    """Serializer for Watchlist model"""
    user = UserSerializer(read_only=True)
    film = FilmSerializer(read_only=True)
    film_id = serializers.PrimaryKeyRelatedField(
        queryset=Film.objects.all(),
        write_only=True,
        source='film'
    )

    class Meta:
        model = Watchlist
        fields = ['id', 'user', 'film', 'film_id', 'added_at']
        read_only_fields = ['id', 'user', 'added_at']

    def create(self, validated_data):
        """Auto-assign current user"""
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)

    def validate_film_id(self, value):
        """Ensure film exists and is not already in watchlist"""
        user = self.context['request'].user
        if Watchlist.objects.filter(user=user, film=value).exists():
            raise serializers.ValidationError("This film is already in your watchlist.")
        return value


class FilmStatsSerializer(serializers.ModelSerializer):
    """Serializer for film statistics (aggregated data)"""
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    rating_distribution = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Film
        fields = ['id', 'title', 'average_rating', 'review_count', 'rating_distribution']

    def get_rating_distribution(self, obj):
        """Get distribution of ratings for this film"""
        from django.db.models import Count
        distribution = {}
        reviews = obj.reviews.values('rating').annotate(count=Count('rating'))
        for item in reviews:
            distribution[str(item['rating'])] = item['count']
        return distribution


class UserReviewStatsSerializer(serializers.ModelSerializer):
    """Serializer for user review statistics"""
    total_reviews = serializers.IntegerField(read_only=True)
    average_rating_given = serializers.FloatField(read_only=True)
    recent_reviews = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'total_reviews', 'average_rating_given', 'recent_reviews']

    def get_recent_reviews(self, obj):
        """Get user's 5 most recent reviews"""
        reviews = obj.reviews.select_related('film').order_by('-created_at')[:5]
        return [
            {
                'id': r.id,
                'film_title': r.film.title,
                'rating': r.rating,
                'created_at': r.created_at
            }
            for r in reviews
        ]
