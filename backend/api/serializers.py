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
    """Сериализатор для создания сессии."""

    movies = MovieSerializer(many=True, read_only=True)

    class Meta:
        model = CustomSession
        fields = ['id',
                  'users',
                  'movies',
                  'matched_movies',
                  'date',
                  'status'
                  ]

    def create(self, validated_data):
        kinopoisk_movies = KinopoiskMovies().get_movies()
        # Проверяем, есть ли фильмы из KinopoiskMovies в нашей базе данных
        existing_movies = Movie.objects.filter(
            id__in=[movie.id for movie in kinopoisk_movies]
        )
        new_movies = {
            movie for movie in kinopoisk_movies
            if movie.id not in existing_movies.values_list(
                'id', flat=True
            )
        }

        # Сохраняет новые фильмы в базе данных
        Movie.objects.bulk_create(
            [Movie(
                id=movie.id,
                name=movie.name,
                genre=movie.genre,
                image=movie.image
            ) for movie in new_movies]
        )

        # Объединяет существующие и новые фильмы
        movies = set(existing_movies) | new_movies
        # Создает новый объект сессии
        session = CustomSession.objects.create(
            users=self.context['request'].user,
            **validated_data
        )
        # Добавляет данные о всех фильмах в создаваемую сессию
        session.movies.set(movies)
        return session

    def to_representation(self, instance):
        """Переопределяем метод для вывода данных сессии."""
        data = super().to_representation(instance)
        data['movies'] = MovieSerializer(instance.movies.all(), many=True).data
        return data


class DraftSessionSerializer(serializers.ModelSerializer):
    """Сериализатор сессии в статусе выбора жанра."""

    users = CustomUserSerializer(many=True, read_only=True)
    movies_genres = GenreSerializer

    class Meta:
        model = CustomSession
        fields = [
            'id',
            'users',
            'movies_genres',
            'date',
            'status',
        ]


class WaitingSessionSerializer(serializers.ModelSerializer):
    """Сериализатор сессии в статусе ожидания всех пользователей."""

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
