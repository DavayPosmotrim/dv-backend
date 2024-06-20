import logging
# from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from custom_sessions.models import CustomSession
from movies.models import Genre, Movie
from services.kinopoisk.kinopoisk_service import KinopoiskMovies
from services.validators import validate_name
from users.models import User


logger = logging.getLogger('api')


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

    genres = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Genre.objects.all()
    )

    class Meta:
        model = Movie
        fields = [
            'id',
            'name',
            'genres',
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
        # genres = self.context.get('genres', [])
        # collections = self.context.get('collections', [])
        genres = validated_data.pop('genres', [])
        collections = validated_data.pop('collections', [])
        kinopoisk_service = KinopoiskMovies(
            genres=genres,
            collections=collections
        )
        kinopoisk_movies_response = kinopoisk_service.get_movies()

        # Логирование ответа от KinopoiskMovies
        logger.debug("KinopoiskMovies response: %s", kinopoisk_movies_response)

        if kinopoisk_movies_response is None:
            raise serializers.ValidationError(
                "Данные о фильмах отсутствуют."
            )
        elif 'docs' not in kinopoisk_movies_response:
            raise serializers.ValidationError(
                "Данные о фильмах имеют неверный формат."
            )

        kinopoisk_movies = kinopoisk_movies_response['docs']

        # Создание или получение жанров и фильмов
        all_movie_ids = []
        for movie_data in kinopoisk_movies:
            genres_list = movie_data.get('genres', [])
            genres_names = [genres['name'] for genres in genres_list if 'name' in genres]

            if not genres_names:
                logger.warning("Жанры отсутствуют для фильма: %s", movie_data.get('name', 'Без названия'))

            genres_objects = [Genre.objects.get_or_create(name=name)[0] for name in genres_names]

            movie_obj, created = Movie.objects.update_or_create(
                id=movie_data['id'],
                defaults={
                    'name': movie_data['name'],
                    'image': movie_data.get('poster', {}).get('url', '')
                }
            )
            movie_obj.genres.set(genres_objects)
            all_movie_ids.append(movie_obj.id)

        session = CustomSession.objects.create(
            # users=user,
            **validated_data
        )
        # Добавляет данные о всех фильмах в создаваемую сессию
        session.movies.set(all_movie_ids)
        return session

    def to_representation(self, instance):
        """Переопределяет метод для вывода данных сессии."""
        data = super().to_representation(instance)
        data['movies'] = MovieSerializer(instance.movies.all(), many=True).data
        return data
