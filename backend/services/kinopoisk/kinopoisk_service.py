import os
from urllib.parse import urljoin

import requests.exceptions
from dotenv import load_dotenv

load_dotenv()


class KinopoiskService:
    """
    Базовый класс сервиса для взаимодействия с API Кинопоиска.

    Атрибуты:
        BASE_URL (str): Базовый URL API Кинопоиска.
        headers (dict): Заголовки для HTTP-запроса, включая API ключ.
        collections_url (str): Полный URL получения коллекций фильмов в API.
        movies_url (str): Полный URL для получения фильмов.
    """

    BASE_URL = os.getenv('KINOPOISK_API_URL')
    headers = {'X-API-KEY': os.getenv('KINOPOISK_API_KEY')}
    collections_url = urljoin(BASE_URL, 'list')
    movies_url = urljoin(BASE_URL, 'movie')

    def _perform_get_request(
        self, url, params: dict[str, str | int | list] = None
    ) -> dict:
        """
        Осуществляет запрос к url API на получение данных.

        :param url: Ссылка при запросе.
        :param params: Query-параметры запроса.
        """

        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()  # Проверка на успешный статус ответа
            try:
                return response.json()
            except ValueError as e:
                # Логирование ошибки, возврат пустого результата или исключения
                print(f"JSON decode error: {e}")
                return None
        except requests.exceptions.RequestException as e:
            # Логирование сетевых ошибок, возврат пустого результата или искл-я
            print(f"Request error: {e}")
            return None


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
        limit: int = 10,
        sort_by_rating: bool = True,
    ):
        """
        Получает пагинированный список фильмов по заданным
        жанрам или коллекциям в виде id и name фильма.

        :param page: Номер страницы.
        :param limit: Максимальное количество элементов на странице.
        :param sort_by_rating: Сортировка по рейтингу от большего к меньшему.
        """

        search_by = 'lists'
        pattern = self.collections
        movie, cartoon, anime = 'movie', 'cartoon', 'anime'
        if self.genres:
            search_by = 'genres.name'
            pattern = list(map(lambda s: s.lower(), self.genres))
            if 'аниме' not in pattern:
                anime = '!anime'
            if 'мультфильм' not in pattern:
                cartoon = '!cartoon'
        if pattern:
            params = {
                search_by: pattern,
                'selectFields': ('id', 'name'),
                'page': page,
                'limit': limit,
                'notNullFields': ('id', 'name'),
                'type': [movie, cartoon, anime],
            }
            if sort_by_rating:
                params['sortField'] = 'rating.kp'
                params['sortType'] = '-1'

            return self._perform_get_request(self.movies_url, params)

        raise ValueError('You should pass either genres or collections')


class KinopoiskCollections(KinopoiskService):
    """Сервис для работы с подборками фильмов на Кинопоиске."""

    def get_collections(self):
        """Получает список подборок, исключая подборки с сериалами."""

        return self._perform_get_request(
            self.collections_url, {'limit': 250, 'category': '!Сериалы'}
        )


class KinopoiskGenres(KinopoiskService):
    """Сервис для получения и управления жанрами фильмов на Кинопоиске."""

    def get_genres(self):
        """
        Получает список возможных жанров из API Кинопоиска.
        Использует специфическую версию API (v1).
        """

        url = f'{self.movies_url}/possible-values-by-field'.replace(
            'v1.4', 'v1'
        )
        return self._perform_get_request(url, {'field': 'genres.name'})


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
            movie['actors'] = []
            movie['directors'] = []
            for person in movie['persons']:
                if person['enProfession'] == 'actor':
                    movie['actors'].append(person)
                elif person['enProfession'] == 'director':
                    movie['directors'].append(person)
            del movie['persons']

    def get_movie(self, movie_id: int):
        """
        Получает информацию о фильме по его ID.
        :param movie_id: ID фильма.
        """

        fields = (
            'id',
            'name',
            'description',
            'year',
            'countries',
            'poster',
            'alternativeName',
            'rating',
            'votes',
            'movieLength',
            'genres',
            'persons',
        )
        params = {'selectFields': fields, 'id': movie_id}
        response = self._perform_get_request(self.movies_url, params)
        self._extract_persons(response['docs'])
        return response['docs'][0]
