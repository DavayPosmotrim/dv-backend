import logging
# from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from custom_sessions.models import CustomSession
from movies.models import Genre, Movie
from services.kinopoisk.kinopoisk_service import KinopoiskMovies
from services.validators import validate_name
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
            # 'id',
            'name'
        ]


class RatingSerializer(serializers.Serializer):
    """Сериализатор для рейтинга фильма."""

    kp = serializers.FloatField()
    imdb = serializers.FloatField()
    tmdb = serializers.FloatField()
    filmCritics = serializers.FloatField()
    russianFilmCritics = serializers.FloatField()


class CountrySerializer(serializers.Serializer):
    """Сериализатор для страны фильма."""

    name = serializers.CharField()


class PersonSerializer(serializers.Serializer):
    """Сериализатор для персоны, связанной с фильмом."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    enName = serializers.CharField()
    description = serializers.CharField()
    profession = serializers.CharField()
    enProfession = serializers.CharField()


class MovieSerializer(serializers.ModelSerializer):
    """Сериализатор краткого представления
    для фильма/списка фильмов."""

    genre = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Genre.objects.all()
    )

    class Meta:
        model = Movie
        fields = [
            'id',
            'name',
            'genre',
            'image',
        ]


class MovieDetailSerializer(serializers.ModelSerializer):
    """Сериализатор детального представления фильма."""

    genre = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Genre.objects.all()
    )
    rating = RatingSerializer()
    countries = CountrySerializer(many=True)
    persons = PersonSerializer(many=True)
    year = serializers.IntegerField()
    description = serializers.CharField()
    shortDescription = serializers.CharField()
    movieLength = serializers.IntegerField()

    class Meta:
        model = Movie
        fields = [
            'id',
            'name',
            'genre',
            'image',
            'rating',
            'countries',
            'persons',
            'year',
            'description',
            'shortDescription',
            'movieLength'
        ]


class CustomSessionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания сессии."""

    genres = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    collections = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    movies = serializers.PrimaryKeyRelatedField(
        many=True, required=False, allow_empty=True,
        read_only=True
    )
    matched_movies = serializers.PrimaryKeyRelatedField(
        many=True, required=False, allow_empty=True,
        read_only=True
    )

    class Meta:
        model = CustomSession
        fields = ['id',
                  #  'users',
                  'movies',
                  'matched_movies',
                  'date',
                  'genres',
                  'collections',
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
        # device_id = self.context['request'].headers.get('device_id')
        # if not device_id:
        #     raise serializers.ValidationError(
        #         {"message": "Требуется device_id"}
        #     )

        # try:
        #     user = User.objects.get(device_id=device_id)
        # except User.DoesNotExist:
        #     raise serializers.ValidationError(
        #         {"message": "Пользователь с указанным device_id не найден"}
        #     )
        genres = self.context.get('genres', [])
        collections = self.context.get('collections', [])
        if genres:
            kinopoisk_movies = KinopoiskMovies(genres=genres)
        elif collections:
            kinopoisk_movies = KinopoiskMovies(collections=collections)
        else:
            raise serializers.ValidationError(
                "Необходимо передать либо genres, либо collections."
            )
        try:
            movies_response = kinopoisk_movies.get_movies()
            if 'items' not in movies_response:
                raise serializers.ValidationError("Ожидаемый формат ответа от API Кинопоиска не найден.")

            kinopoisk_movies = [
                Movie(id=movie['id'], name=movie['name'], genre=','.join([genre['name'] for genre in movie['genres']]), image=movie['poster'])
                for movie in movies_response['items']
            ]
        except ValueError as e:
            logging.error(f"Error getting movies from Kinopoisk: {e}")
            raise serializers.ValidationError(str(e))
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
            # users=user,
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
