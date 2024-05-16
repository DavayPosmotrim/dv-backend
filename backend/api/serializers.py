from rest_framework import serializers

from custom_sessions.models import CustomSession, UserMovieVote
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
    movie_votes = serializers.SerializerMethodField()

    class Meta:
        model = CustomSession
        fields = [
            'id',
            'users',
            'movies',
            'date',
            'status',
            'movie_votes'
            'matched_movies',
        ]

    def get_movie_votes(self, obj):
        """Принимает объект сессии,
        сохраняет голоса пользователей по фильмам. """
        votes = UserMovieVote.objects.filter(
            session=obj
        ).values_list('movie__id', 'user__id')
        movie_votes = {
            movie: users for movie, users in votes.distinct()
        }
        return movie_votes

    def get_matched_movies(self, obj):
        """Принимает объект сессии, считает голоса пользователей
        за фильм и выдает совпадения (сохраняет в мэтчи),
        если проголосовали все пользователи в комнате."""
        num_users_in_session = obj.users.count()
        movie_votes = self.get_movie_votes(obj)
        matched_movies = [
            movie for movie, users in movie_votes.items()
            if len(users) == num_users_in_session
        ]
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
        fields = ['id', 'name', 'genre', 'image']
