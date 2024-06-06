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
        fields = ['id', 'movies', 'matched_movies', 'date', 'status', 'users']

    def create(self, validated_data):
        genres = self.context.get('genres', [])
        collections = self.context.get('collections', [])
        kinopoisk_movies = KinopoiskMovies(
            genres=genres,
            collections=collections
        )
        movies_data = kinopoisk_movies.get_movies()
        # поиск фильмов в собственной БД
        existing_movies = Movie.objects.filter(
            id__in=[movie['id'] for movie in movies_data]
        )
        existing_movies_ids = [movie.id for movie in existing_movies]
        # поиск фильмов на кинопоиске, сохранение их в БД
        new_movies_data = [
            movie for movie in movies_data
            if movie['id'] not in existing_movies_ids
        ]
        new_movies = [
            Movie(
                id=movie['id'],
                name=movie['name'],
                genre=movie['genre'],
                image=movie['image']
            )
            for movie in new_movies_data
        ]
        Movie.objects.bulk_create(new_movies)
        session = CustomSession.objects.create(
            **validated_data,
            movies=Movie.objects.filter(
                id__in=[movie['id'] for movie in movies_data]
            )
        )
        return session


class WaitingSessionSerializer(serializers.ModelSerializer):
    """Сериализатор сессии в статусе ожидания."""

    users = CustomUserSerializer(many=True, read_only=True)

    class Meta:
        model = CustomSession
        fields = [
            'id',
            'users',
            'movies',
            'date',
            'status',
        ]


class VotingSessionSerializer(serializers.ModelSerializer):
    """Сериализатор сессии в статусе голосования."""

    users = CustomUserSerializer(many=True, read_only=True)

    class Meta:
        model = CustomSession
        fields = [
            'id',
            'users',
            'movies',
            'matched_movies',
            'date',
            'status'
        ]


class ClosedSessionSerializer(serializers.ModelSerializer):
    """Сериализатор закрытой сессии."""

    users = CustomUserSerializer(many=True, read_only=True)

    class Meta:
        model = CustomSession
        fields = [
            'id',
            'users',
            'matched_movies',
            'date',
            'status'
        ]
