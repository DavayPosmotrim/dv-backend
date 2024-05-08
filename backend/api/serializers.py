from collections import Counter
from itertools import chain
from rest_framework import serializers

from services.validators import validate_name
from custom_sessions.models import CustomSession
from movies.models import Genre, Movie
from users.models import User


class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer for user."""

    class Meta:
        model = User
        fields = ('name', 'device_id')
        extra_kwargs = {
            'device_id': {'write_only': True},  # Hide device_id from responses
        }

    def validate(self, data):
        # Automatically assign device_id from request context
        data['device_id'] = self.context.get('device_id')
        validate_name(data['name'])
        return data


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор жанра."""

    class Meta:
        model = Genre
        fields = [
            'id',
            'name'
        ]


class CustomSessionSerializer(serializers.ModelSerializer):
    """Сериализатор сеанса/комнаты."""

    matched_movies = serializers.SerializerMethodField()

    class Meta:
        model = CustomSession
        fields = [
            'id',
            'users',
            'movies',
            'date',
            'status',
            'matched_movies',
        ]

    def get_matched_movies(self, obj):
        """Принимает объект сессии, считает голоса пользователей
        за фильм и выдает совпадения (сохраняет в мэтчи),
        если голосов больше 1."""
        movies = obj.movies.all()
        user_movie_votes = chain.from_iterable(
            movies.values_list('users', flat=True)
        )
        movie_vote_counts = Counter(user_movie_votes)
        matched_movie_ids = [
            movie.id for movie in movies
            if movie_vote_counts[movie.id] > 1
        ]
        matched_movies = movies.filter(id__in=matched_movie_ids)
        return MovieSerializer(matched_movies, many=True).data


class MovieSerializer(serializers.ModelSerializer):
    """Сериализатор фильма/списка фильмов."""

    genre = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Genre.objects.all()
    )

    class Meta:
        model = Movie
        fields = ['id', 'name', 'genre']
