import logging
from typing import Any, Optional, Union

import requests.exceptions
from custom_sessions.models import CustomSession, CustomSessionMovieVote
from movies.models import Collection, Genre, Movie
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from services.kinopoisk.kinopoisk_service import (KinopoiskMovieInfo,
                                                  KinopoiskMovies)
from services.validators import validate_name
from users.models import User

logger = logging.getLogger("serializers")


class CreateVoteSerializer(serializers.ModelSerializer):
    """Serializer to add votes."""
    class Meta:
        model = CustomSessionMovieVote
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(
                queryset=CustomSessionMovieVote.objects.all(),
                fields=["session_id", "user_id", "movie_id"],
                message="Вы уже проголосовали за этот фильм"
            )
        ]


class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer for user."""

    class Meta:
        model = User
        fields = ("name", "device_id")
        extra_kwargs = {
            "device_id": {"read_only": True},
        }

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        # Automatically assign device_id from request context
        data["device_id"] = self.context.get("device_id")
        validate_name(data["name"])
        return data


class CollectionSerializer(serializers.ModelSerializer):
    """Сериализатор подборки."""

    cover = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = ["name", "slug", "cover"]

    def get_cover(self, obj: Collection) -> str | None:
        if "cover" in obj and "url" in obj["cover"]:
            return obj["cover"]["url"]
        else:
            return None


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор жанра."""

    class Meta:
        model = Genre
        fields = ["name"]


class MovieSerializer(serializers.ModelSerializer):
    """Сериализатор краткого представления
    для фильма в списке фильмов."""

    class Meta:
        model = Movie
        fields = ["id", "name", "poster"]


class MovieDetailSerializer(serializers.ModelSerializer):
    """Сериализатор создания и детального представления фильма."""

    genres: list[GenreSerializer] = GenreSerializer(many=True)

    class Meta:
        model = Movie
        fields = [
            "id",
            "name",
            "description",
            "year",
            "countries",
            "poster",
            "alternative_name",
            "rating_kp",
            "rating_imdb",
            "votes_kp",
            "votes_imdb",
            "movie_length",
            "genres",
            "directors",
            "actors",
        ]

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Преобразование данных из внешнего источника в формат модели."""
        movie_data = data.get("movie_data", {})
        # logger.debug(f"Movie data incoming: {movie_data}")
        poster_data = movie_data.get("poster", {})
        countries_list = movie_data.get("countries", [])
        rating_data = movie_data.get("rating", {})
        votes_data = movie_data.get("votes", {})
        genres = []
        for genre in movie_data.get("genres", []):
            genre_name = genre.get("name", "")
            if genre_name:
                genre_obj, created = Genre.objects.get_or_create(
                    name=genre_name
                )
                genres.append(genre_obj)
        countries = ([country.get("name", "") for country in countries_list])
        validated_data = {
            "genres": genres,
            "name": movie_data.get("name", ""),
            "poster": poster_data.get("url", ""),
            "description": movie_data.get("description", ""),
            "year": movie_data.get("year"),
            "countries": countries,
            "actors": movie_data.get("actors"),
            "directors": movie_data.get("directors"),
            "alternative_name": movie_data.get("alternativeName", ""),
            "rating_kp": rating_data.get("kp", 0),
            "rating_imdb": rating_data.get("imdb", 0),
            "votes_kp": votes_data.get("kp", 0),
            "votes_imdb": votes_data.get("imdb", 0),
            "movie_length": movie_data.get("movieLength"),
        }
        # logger.debug(f"Validated data: {validated_data}")
        return validated_data

    def check_and_add_movies(
        self, kinopoisk_movies: Optional[list[dict[str, Any]]]
    ) -> list[int]:
        """Проверка наличия фильма в базе данных
        и добавление фильма в БД при отсутствии."""
        if kinopoisk_movies is None:
            return []
        all_movie_ids = []
        for movie_data in kinopoisk_movies:
            movie_id = movie_data["id"]
            if not Movie.objects.filter(id=movie_id).exists():
                logger.debug(f"Фильм {movie_id} отсутствует в базе данных.")
                self.create_movie(movie_data)
                all_movie_ids.append(movie_id)
            else:
                logger.debug(f"Фильм {movie_id} найден в базе данных.")
                all_movie_ids.append(movie_id)

        return all_movie_ids

    def fetch_kinopoisk_movies(
        self, genres: list[str], collections: list[str]
    ) -> list[dict[str, Any]]:
        """Получение данных с кинопоиска."""
        kinopoisk_service = KinopoiskMovies(
            genres=genres,
            collections=collections
        )
        try:
            kinopoisk_movies_response = kinopoisk_service.get_movies()
            if kinopoisk_movies_response is None:
                raise serializers.ValidationError(
                    "Данные о фильмах отсутствуют."
                )
            elif "docs" not in kinopoisk_movies_response:
                raise serializers.ValidationError(
                    "Данные о фильмах имеют неверный формат."
                )
            kinopoisk_movies = kinopoisk_movies_response["docs"]
            if kinopoisk_movies is not None:
                KinopoiskMovieInfo._extract_persons(kinopoisk_movies)
            logger.debug(
                f"Movies from Kinopoisk (first 2): {kinopoisk_movies[:2]}"
            )
            return kinopoisk_movies
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к Кинопоиску: {e}")
            if (
                isinstance(e, requests.exceptions.HTTPError)
                and e.response.status_code == 504
            ):
                raise serializers.ValidationError(
                    "Сервер Кинопоиска не отвечает. Попробуйте позже."
                )
            else:
                raise serializers.ValidationError(
                    "Ошибка при запросе к Кинопоиску."
                )

    def create_movie(self, movie_data: dict[str, Any]) -> Movie:
        """Создание или обновление фильма
        на основе валидированных данных."""
        # logger.debug(f"Creating or updating movie with data: {movie_data}")

        validated_data = self.validate(
            {"movie_data": movie_data}
        )
        movie_id = movie_data["id"]
        movie_obj, created = Movie.objects.update_or_create(
            id=movie_id,
            defaults={
                "name": validated_data.get("name"),
                "poster": validated_data.get("poster"),
                "description": validated_data.get("description"),
                "year": validated_data.get("year"),
                "alternative_name": validated_data.get("alternative_name"),
                "rating_kp": validated_data.get("rating_kp"),
                "rating_imdb": validated_data.get("rating_imdb"),
                "votes_kp": validated_data.get("votes_kp"),
                "votes_imdb": validated_data.get("votes_imdb"),
                "movie_length": validated_data.get("movie_length"),
                "actors": validated_data.get("actors", []),
                "directors": validated_data.get("directors", []),
                "countries": validated_data.get("countries", [])
            }
        )
        genres = validated_data.pop("genres", [])
        if genres:
            movie_obj.genres.set(genres)

        return movie_obj


class MovieRouletteSerializer(serializers.ModelSerializer):
    """Сериализатор представления фильма для рулетки."""

    genres: list[GenreSerializer] = GenreSerializer(many=True)

    class Meta:
        model = Movie
        fields = [
            "name",
            "year",
            "countries",
            "poster",
            "alternative_name",
            "rating_kp",
            "movie_length",
            "genres",
        ]


class CustomSessionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания сессии."""

    genres = serializers.ListField(
        child=serializers.CharField(), required=False, write_only=True
    )
    collections = serializers.ListField(
        child=serializers.CharField(), required=False, write_only=True
    )
    movies = serializers.PrimaryKeyRelatedField(
        many=True, required=False, read_only=True
    )
    matched_movies = serializers.PrimaryKeyRelatedField(
        many=True, required=False, allow_empty=True, read_only=True
    )
    users = CustomUserSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = CustomSession
        fields = [
            "id",
            "users",
            "movies",
            "matched_movies",
            "date",
            "genres",
            "collections",
            "status",
            "image",
        ]

    def validate_id(self, value: str) -> str:
        """
        Проверяет уникальность сгенерированного идентификатора сессии.
        """
        if CustomSession.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                "Не удалось сгенерировать уникальный идентификатор."
            )
        return value

    def create(self, validated_data: dict[str, Any]) -> CustomSession:
        request = self.context.get("request")
        device_id = request.headers.get("Device-Id")
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
        genres = validated_data.pop("genres", [])
        collections = validated_data.pop("collections", [])
        # logger.debug(f"Genres from request: {genres}")
        # logger.debug(f"Collections from request: {collections}")
        movie_detail_serializer = MovieDetailSerializer()
        kinopoisk_movies = movie_detail_serializer.fetch_kinopoisk_movies(
            genres, collections
        )
        all_movie_ids = movie_detail_serializer.check_and_add_movies(
            kinopoisk_movies
        )
        # logger.debug(f"All movie IDs: {all_movie_ids}")
        session = CustomSession.objects.create(**validated_data)
        session.users.add(user)
        session.movies.set(all_movie_ids)
        return session

    def to_representation(self, instance: CustomSession) -> dict[str, Any]:
        """Переопределяет метод для вывода данных сессии."""
        data = super().to_representation(instance)
        data["movies"] = MovieDetailSerializer(instance.movies, many=True).data
        return data


class CustomSessionSerializer(serializers.ModelSerializer):
    "Serializer for closed sessions."
    users = serializers.StringRelatedField(many=True, read_only=True)
    mathced_movies = MovieDetailSerializer(many=True, read_only=True)
    mathced_movies_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomSession
        fields = [
            "id",
            "users",
            "matched_movies",
            "date",
            "image",
            "mathced_movies_count",
        ]

    def get_mathced_movies_count(self, obj: CustomSession) -> int:
        return obj.matched_movies.count()
