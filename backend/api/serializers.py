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

    def validate_id(self, value):
        """
        Проверяет уникальность сгенерированного идентификатора сессии.
        """
        if CustomSession.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                "Не удалось сгенерировать уникальный идентификатор."
            )
        return value

    def create(self, validated_data):
        genres = self.context.get('genres', [])
        collections = self.context.get('collections', [])
        kinopoisk_movies = KinopoiskMovies(
            genres=genres,
            collections=collections
        )
        kinopoisk_movies = KinopoiskMovies().get_movies()
        if kinopoisk_movies is None:
            raise serializers.ValidationError(
                "Данные о фильмах отсутствуют в контексте."
            )
        # Проверяет, есть ли фильмы из KinopoiskMovies в нашей базе данных
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
        """Переопределяет метод для вывода данных сессии."""
        data = super().to_representation(instance)
        data['movies'] = MovieSerializer(instance.movies.all(), many=True).data
        return data
