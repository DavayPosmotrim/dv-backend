from custom_sessions.models import CustomSession
from movies.models import Genre, Movie
from rest_framework import serializers
from services.kinopoisk.kinopoisk_service import KinopoiskMovies
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


class CustomSessionCreateSerializer(serializers.ModelSerializer):
    movies = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Movie.objects.all()
    )
    users = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all()
    )
    id = serializers.CharField(read_only=True)

    class Meta:
        model = CustomSession
        fields = ['id', 'movies', 'date', 'status', 'users']

    def create(self, validated_data):
        genres = self.context.get('genres', [])
        collections = self.context.get('collections', [])
        kinopoisk_movies = KinopoiskMovies(
            genres=genres,
            collections=collections
        )
        session = CustomSession.objects.create(
            **validated_data,
            movies=Movie.objects.filter(
                id__in=[movie['id'] for movie in kinopoisk_movies.get_movies()]
            )
        )
        return session


class CustomSessionSerializer(serializers.ModelSerializer):
    """Сериализатор сеанса/комнаты."""

    users = CustomUserSerializer(many=True, read_only=True)

    class Meta:
        model = CustomSession
        fields = [
            'id',
            'users',
            'movies',
            'date',
            'status',
            'movie_votes',
            'matched_movies',
        ]
