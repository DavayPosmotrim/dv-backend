import logging

import requests.exceptions
from custom_sessions.models import CustomSession
from movies.models import Collection, Genre, Movie
from rest_framework import serializers
from services.kinopoisk.kinopoisk_service import (KinopoiskMovieInfo,
                                                  KinopoiskMovies)
from services.validators import validate_name
from users.models import User

logger = logging.getLogger('serializers')


class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer for user."""

    class Meta:
        model = User
        fields = ('name', 'device_id')
        extra_kwargs = {
            'device_id': {'read_only': True},
        }

    def validate(self, data):
        # Automatically assign device_id from request context
        data['device_id'] = self.context.get('device_id')
        validate_name(data['name'])
        return data


class CollectionSerializer(serializers.ModelSerializer):
    """Сериализатор подборки."""

    cover = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = [
            'name',
            'slug',
            'cover'
        ]

    def get_cover(self, obj):
        return (
            obj['cover']['url'] if 'cover' in obj
            and 'url' in obj['cover'] else None
        )


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор жанра."""

    class Meta:
        model = Genre
        fields = [
            'name'
        ]


class MovieSerializer(serializers.ModelSerializer):
    """Сериализатор краткого представления
    для фильма в списке фильмов."""

    class Meta:
        model = Movie
        fields = [
            'id',
            'name',
            'poster'
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
            'alternative_name',
            'rating_kp',
            'rating_imdb',
            'votes_kp',
            'votes_imdb',
            'movie_length',
            'genres',
            'directors',
            'actors',
        ]


class MovieRouletteSerializer(serializers.ModelSerializer):
    """Сериализатор представления фильма для рулетки."""

    genres = GenreSerializer(many=True)

    class Meta:
        model = Movie
        fields = [
            'name',
            'year',
            'countries',
            'poster',
            'alternative_name',
            'rating_kp',
            'movie_length',
            'genres'
        ]


class CustomSessionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания сессии."""

    genres = serializers.ListField(
        child=serializers.CharField(), required=False,
        write_only=True
    )
    collections = serializers.ListField(
        child=serializers.CharField(), required=False,
        write_only=True
    )
    movies = serializers.PrimaryKeyRelatedField(
        many=True, required=False,
        read_only=True
    )
    matched_movies = serializers.PrimaryKeyRelatedField(
        many=True, required=False, allow_empty=True,
        read_only=True
    )
    users = CustomUserSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = CustomSession
        fields = ['id',
                  'users',
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
        request = self.context.get('request')
        device_id = request.headers.get('Device-Id')
        if not device_id:
            raise serializers.ValidationError(
                {"message": "Требуется device_id"}
            )

        try:
            user = User.objects.get(device_id=device_id)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"message": "Пользователь с указанным Device-Id не найден"}
            )
        genres = validated_data.pop('genres', [])
        collections = validated_data.pop('collections', [])
        logger.debug(f"Genres from request: {genres}")
        logger.debug(f"Collections from request: {collections}")
        kinopoisk_service = KinopoiskMovies(
            genres=genres,
            collections=collections
        )
        try:
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
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к Кинопоиску: {e}")
            if isinstance(
                e, requests.exceptions.HTTPError
            ) and e.response.status_code == 504:
                raise serializers.ValidationError(
                    "Сервер Кинопоиска не отвечает. Попробуйте позже."
                )
            else:
                raise serializers.ValidationError(
                    "Ошибка при запросе к Кинопоиску."
                )
        kinopoisk_movies = kinopoisk_movies_response['docs']
        logger.debug(
            f"Movies from Kinopoisk (first 3): {kinopoisk_movies[:3]}"
        )

        all_movie_ids = []
        for movie_data in kinopoisk_movies:
            movie_id = movie_data['id']
            detailed_movie_data = self.get_movie_details(movie_id)
            # Получение фильма из БД или сохранение в нее
            movie_obj, created = Movie.objects.get_or_create(
                id=movie_id,
            )
            if created:
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
                poster_data = detailed_movie_data.get('poster', {})
                countries_list = detailed_movie_data.get('countries', [])
                countries = [country['name'] for country in countries_list]
                rating_data = detailed_movie_data.get('rating', {})
                votes_data = detailed_movie_data.get('votes', {})
                actors = detailed_movie_data.get('actors', []),
                directors = detailed_movie_data.get('directors', []),
                movie_obj.name = movie_data.get('name', '')
                movie_obj.poster = poster_data.get('url', '')
                movie_obj.description = detailed_movie_data.get(
                    'description', ''
                )
                movie_obj.year = detailed_movie_data.get('year', None)
                movie_obj.countries = countries
                movie_obj.alternative_name = detailed_movie_data.get(
                    'alternativeName', ''
                )
                movie_obj.rating_kp = rating_data.get('kp', None)
                movie_obj.rating_imdb = rating_data.get('imdb', None)
                movie_obj.votes_kp = votes_data.get('kp', None)
                movie_obj.votes_imdb = votes_data.get('imdb', None)
                movie_obj.movie_length = detailed_movie_data.get(
                    'movieLength', None
                )
                movie_obj.actors = actors
                movie_obj.directors = directors
                movie_obj.genres.set(genre_objects)
                movie_obj.save()
            all_movie_ids.append(movie_obj.id)
        session = CustomSession.objects.create(
            **validated_data
        )
        # Добавление данных о всех фильмах в создаваемую сессию
        session.users.add(user)
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
        data['movies'] = MovieDetailSerializer(
            instance.movies, many=True
        ).data
        return data
