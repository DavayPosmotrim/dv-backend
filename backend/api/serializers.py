from custom_sessions.models import CustomSession
from movies.models import Genre, Movie
from rest_framework import serializers
from services.kinopoisk.kinopoisk_service import (KinopoiskMovieInfo,
                                                  KinopoiskMovies)
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
            'alternative_name',
            'rating_kp',
            'rating_imdb',
            'movie_length',
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
                  'genres',
                  'collections',
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
        kinopoisk_service = KinopoiskMovies(
            genres=genres,
            collections=collections
        )
        kinopoisk_movies_response = kinopoisk_service.get_movies()
        if kinopoisk_movies_response is None:
            raise serializers.ValidationError(
                "Данные о фильмах отсутствуют."
            )
        elif 'docs' not in kinopoisk_movies_response:
            raise serializers.ValidationError(
                "Данные о фильмах имеют неверный формат."
            )
        kinopoisk_movies = kinopoisk_movies_response['docs']

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
            # Извлечение URL постера
            poster_data = detailed_movie_data.get('poster', {})
            poster_url = poster_data.get('url', '')
            # Извлечение дополнительных полей
            description = detailed_movie_data.get('description', '')
            year = detailed_movie_data.get('year', None)
            countries_list = detailed_movie_data.get('countries', [])
            countries = ', '.join(
                [country['name'] for country in countries_list]
            )
            alternative_name = detailed_movie_data.get('alternativeName', '')
            rating_data = detailed_movie_data.get('rating', {})
            rating_kp = rating_data.get('kp', None)
            rating_imdb = rating_data.get('imdb', None)
            movie_length = detailed_movie_data.get('movieLength', None)
            persons_list = detailed_movie_data.get('persons', [])
            persons = [
                {
                    'name': person['name'],
                    'enProfession': person['enProfession']
                } for person in persons_list
            ]
            # Получение фильма из БД или сохранение в нее
            movie_obj, created = Movie.objects.get_or_create(
                id=movie_id,
            )

            if created or not movie_obj.name or not movie_obj.poster:
                movie_obj.name = movie_data.get('name', '')
                movie_obj.poster = poster_url
                movie_obj.description = description
                movie_obj.year = year
                movie_obj.countries = countries
                movie_obj.alternative_name = alternative_name
                movie_obj.rating_kp = rating_kp
                movie_obj.rating_imdb = rating_imdb
                movie_obj.movie_length = movie_length
                movie_obj.persons = persons
                movie_obj.genres.set(genre_objects)
                movie_obj.save()

            all_movie_ids.append(movie_obj.id)
        # Создает новый объект сессии
        session = CustomSession.objects.create(
            # users=user,
            **validated_data
        )
        # Добавляет данные о всех фильмах в создаваемую сессию
        session.movies.set(all_movie_ids)
        return session

    def get_movie_details(self, movie_id):
        """Выполняет запрос к API Кинопоиска для получения
        детальной информации о фильме."""
        kinopoisk_movie_info_service = KinopoiskMovieInfo()
        detailed_movie_data = kinopoisk_movie_info_service.get_movie(
            movie_id
        )
        return detailed_movie_data

    def to_representation(self, instance):
        """Переопределяет метод для вывода данных сессии."""
        data = super().to_representation(instance)
        data['movies'] = MovieDetailSerializer(
            instance.movies.all(), many=True
        ).data
        return data
