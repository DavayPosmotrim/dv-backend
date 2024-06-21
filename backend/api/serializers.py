import logging
# from django.shortcuts import get_object_or_404
from rest_framework import serializers

from custom_sessions.models import CustomSession
from movies.models import Genre, Movie
from services.kinopoisk.kinopoisk_service import (KinopoiskMovies,
                                                  KinopoiskMovieInfo)
from services.validators import validate_name
from users.models import User


logger = logging.getLogger('serializers')


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

    genres = GenreSerializer(many=True)

    class Meta:
        model = Movie
        fields = [
            'id',
            'name',
            'genres',
            'poster',
        ]


class MovieDetailSerializer(serializers.ModelSerializer):
    """Сериализатор детального представления фильма."""

    genres = GenreSerializer(many=True)

    class Meta:
        model = Movie
        fields = [
            'id',
            'name',
            'description',
            'year',
            'countries',
            'poster',
            'alternativeName',
            'rating',
            'movieLength',
            'genres',
            'persons',
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
        genres = validated_data.pop('genres', [])
        collections = validated_data.pop('collections', [])
        logger.debug(f"Genres from request: {genres}")
        logger.debug(f"Collections from request: {collections}")
        kinopoisk_service = KinopoiskMovies(
            genres=genres,
            collections=collections
        )
        kinopoisk_movies_response = kinopoisk_service.get_movies()
        logger.debug(f"Фильмы с кинопоиска-1: {kinopoisk_movies_response}")
        if kinopoisk_movies_response is None:
            raise serializers.ValidationError(
                "Данные о фильмах отсутствуют."
            )
        elif 'docs' not in kinopoisk_movies_response:
            raise serializers.ValidationError(
                "Данные о фильмах имеют неверный формат."
            )
        kinopoisk_movies = kinopoisk_movies_response['docs']
        logger.debug(
            f"Movies from Kinopoisk (first 3): {kinopoisk_movies[:3]}"
        )

        # Создание или получение фильмов
        all_movie_ids = []
        for movie_data in kinopoisk_movies:
            movie_id = movie_data['id']
            detailed_movie_data = self.get_movie_details(movie_id)
            # Извлечение жанров
            movie_genres = detailed_movie_data.get('genres', [])
            genre_objects = []
            for genre in movie_genres:
                genre_name = genre.get('name', '')
                if genre_name:
                    genre_obj, created = Genre.objects.get_or_create(
                        name=genre_name
                    )
                    genre_objects.append(genre_obj)
            logger.debug(
                f"Genres for movie {movie_data['id']}: {genre_objects}"
            )
            # Извлечение URL постера
            poster_data = detailed_movie_data.get('poster', {})
            poster_url = poster_data.get('url', '')
            # Получение фильма из БД или сохранение в нее
            movie_obj, created = Movie.objects.get_or_create(
                id=movie_id,
            )

            if created or not movie_obj.name or not movie_obj.poster:
                movie_obj.name = movie_data.get('name', '')
                movie_obj.poster = poster_url
                movie_obj.genres.set(genre_objects)
                movie_obj.save()

            all_movie_ids.append(movie_obj.id)

        session = CustomSession.objects.create(
            # users=user,
            **validated_data
        )
        # Добавление данные о всех фильмах в создаваемую сессию
        session.movies.set(all_movie_ids)
        return session

    def get_movie_details(self, movie_id):
        """Выполняет запрос к API Кинопоиска для получения
        детальной информации о фильме."""
        kinopoisk_movie_info_service = KinopoiskMovieInfo()
        try:
            detailed_movie_data = kinopoisk_movie_info_service.get_movie(
                movie_id
            )
        except KeyError as e:
            logger.error(f"KeyError: {e} for movie_id: {movie_id}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error: {e} for movie_id: {movie_id}")
            return {}

        return detailed_movie_data

    def to_representation(self, instance):
        """Переопределяет метод для вывода данных сессии."""
        data = super().to_representation(instance)
        data['movies'] = MovieSerializer(instance.movies, many=True).data
        return data
