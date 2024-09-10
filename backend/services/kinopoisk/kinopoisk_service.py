import logging
import os
from urllib.parse import urljoin

import requests.exceptions
from dotenv import load_dotenv
from services.constants import MAX_MOVIES_QUANTITY

load_dotenv()
logger = logging.getLogger('kinopoisk')


class KinopoiskService:
    """
    Базовый класс сервиса для взаимодействия с API Кинопоиска.

    Атрибуты:
        BASE_URL (str): Базовый URL API Кинопоиска.
        headers (dict): Заголовки для HTTP-запроса, включая API ключ.
        collections_url (str): Полный URL получения коллекций фильмов в API.
        movies_url (str): Полный URL для получения фильмов.
    """

    BASE_URL = os.getenv("KINOPOISK_API_URL")
    headers = {"X-API-KEY": os.getenv("KINOPOISK_API_KEY")}
    collections_url = urljoin(BASE_URL, "list")
    movies_url = urljoin(BASE_URL, "movie")

    def _perform_get_request(
        self, url, params: dict[str, str | int | list] = None
    ) -> dict:
        """
        Осуществляет запрос к url API на получение данных.

        :param url: Ссылка при запросе.
        :param params: Query-параметры запроса.
        """

        response = requests.get(url, params=params, headers=self.headers)
        return response.json()


class KinopoiskMovies(KinopoiskService):
    """Сервис для получения информации о фильмах с возможностью фильтрации."""

    def __init__(
        self,
        genres: list | tuple = None,
        collections: list | tuple = None,
    ):
        self.genres = genres
        self.collections = collections

    def get_movies(
        self,
        page: int = 1,
        limit: int = 250,
        sort_by_rating: bool = True,
    ):
        """
        Получает пагинированный список фильмов по заданным
        жанрам или коллекциям в виде id и name фильма.

        :param page: Номер страницы.
        :param limit: Максимальное количество элементов на странице.
        :param sort_by_rating: Сортировка по рейтингу от большего к меньшему.
        """

        search_by = "lists"
        pattern = self.collections
        movie, cartoon, anime = ["movie", "cartoon", "anime"]
        if self.genres:
            search_by = "genres.name"
            pattern = list(map(lambda s: s.lower(), self.genres))
            if "аниме" not in pattern:
                anime = "!anime"
            if "мультфильм" not in pattern:
                cartoon = "!cartoon"
        if pattern:
            params = {
                search_by: pattern,
                "selectFields": (
                    "id",
                    "name",
                    "description",
                    "year",
                    "countries",
                    "poster",
                    "alternativeName",
                    "rating",
                    "votes",
                    "movieLength",
                    "genres",
                    "persons"
                ),
                "page": page,
                "limit": limit,
                "notNullFields": ("id", "name"),
                "type": [movie, cartoon, anime,
                         "!animated-series",
                         "!tv-series"],
                "isSeries": False
            }
            if sort_by_rating:
                params["sortField"] = "rating.kp"
                params["sortType"] = "-1"

            return self._perform_get_request(self.movies_url, params)

        raise ValueError("You should pass either genres or collections")

    def get_all_movies(
            self,
            limit_per_page: int = 250,
            max_movies: int = MAX_MOVIES_QUANTITY
    ):
        """Получение всех фильмов с использованием пагинации."""
        all_movies = []
        page = 1
        try:
            while len(all_movies) < max_movies:
                kinopoisk_movies_response = self.get_movies(
                    page=page, limit=limit_per_page
                )
                if kinopoisk_movies_response is None:
                    raise ValueError("Данные о фильмах отсутствуют.")
                elif "docs" not in kinopoisk_movies_response:
                    raise ValueError("Данные о фильмах имеют неверный формат.")
                kinopoisk_movies = kinopoisk_movies_response["docs"]
                if not kinopoisk_movies:
                    break
                all_movies.extend(kinopoisk_movies)
                page += 1
                if len(kinopoisk_movies) < limit_per_page:
                    break
            return all_movies[:max_movies]
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к Кинопоиску: {e}")
            raise e


class KinopoiskCollections(KinopoiskService):
    """Сервис для работы с подборками фильмов на Кинопоиске."""

    def get_collections(self):
        """Получает список подборок, исключая подборки с сериалами."""

        return self._perform_get_request(
            self.collections_url, {"limit": 250, "category": "!Сериалы"}
        )


class KinopoiskGenres(KinopoiskService):
    """Сервис для получения и управления жанрами фильмов на Кинопоиске."""

    def get_genres(self):
        """
        Получает список возможных жанров из API Кинопоиска.
        Использует специфическую версию API (v1).
        """

        url = f"{self.movies_url}/possible-values-by-field".replace("v1.4",
                                                                    "v1")
        return self._perform_get_request(url, {"field": "genres.name"})


class KinopoiskMovieInfo(KinopoiskService):
    """Сервис для получения детальной информации о фильмах на Кинопоиске."""

    @staticmethod
    def _extract_persons(movies: list):
        """
        Извлекает актеров и режиссеров из поля persons,
        добавляя их в список в соответствующие поля.

        :param movies: Список фильмов из ответа API.
        """

        for movie in movies:
            movie["actors"] = []
            movie["directors"] = []
            actor_count = 0
            director_count = 0
            # Используем get с пустым списком по умолчанию
            persons = movie.get("persons", [])

            for person in persons:
                # Если нет имени на русском, заменяем на оригинальное
                name = person.get("name") or person.get("enName")
                if person.get("enProfession") == "actor" and actor_count < 4:
                    movie["actors"].append(name)
                    actor_count += 1
                elif person.get(
                    "enProfession"
                ) == "director" and director_count < 4:
                    movie["directors"].append(name)
                    director_count += 1

            # Если списки пусты, заменяем их на None
            if not movie["actors"]:
                movie["actors"] = None
            if not movie["directors"]:
                movie["directors"] = None

            # Удаляем ключ только если он существует
            if "persons" in movie:
                del movie["persons"]

    def get_movie(self, movie_id: int):
        """
        Получает информацию о фильме по его ID.
        :param movie_id: ID фильма.
        """

        fields = (
            "id",
            "name",
            "description",
            "year",
            "countries",
            "poster",
            "alternativeName",
            "rating",
            "votes",
            "movieLength",
            "genres",
            "persons",
        )
        params = {"selectFields": fields, "id": movie_id}
        response = self._perform_get_request(self.movies_url, params)
        self._extract_persons(response["docs"])
        return response["docs"][0]
