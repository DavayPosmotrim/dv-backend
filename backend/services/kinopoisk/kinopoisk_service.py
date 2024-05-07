import os
from pprint import pprint
from urllib.parse import urljoin

import requests.exceptions
from dotenv import load_dotenv

load_dotenv()


class KinopoiskService:
    """
    Класс сервиса для взаимодействия с API Кинопоиска.

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

        response = requests.get(url, params=params, headers=self.headers)
        return response.json()

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

    def _get_filtered_movies(self, params: dict, fields: list | tuple):
        """
        Получает список фильмов с требуемыми полями,

        перезаписывая актеров и режиссеров в отдельные поля.
        :param fields: Требуемые поля фильма в ответе.
        """

        params['selectFields'] = fields
        response = self._perform_get_request(self.movies_url, params)
        return response

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
            'movieLength',
            'genres',
            'persons',
        )
        response = self._get_filtered_movies({'id': movie_id}, fields)
        self._extract_persons(response['docs'])
        return response['docs'][0]

    def get_collections(self):
        """Получает список подборок."""

        return self._perform_get_request(self.collections_url, {'limit': 250})

    def get_movies_from_collections(
        self, collections: list | tuple, page: int = 1, limit: int = 10
    ):
        """
        Получает пагинированный список фильмов из данных коллекций.

        :param collections: Список slug коллекций фильмов.
        :param page: Номер страницы.
        :param limit: Максимальное количество элементов на странице.
        """

        return self._get_filtered_movies(
            params={
                'lists': collections,
                'page': page,
                'limit': limit,
            },
            fields=('id', 'name'),
        )

    def get_genres(self):
        """
        Получает список возможных жанров из API Кинопоиска.
        Использует специфическую версию API (v1).
        """

        url = f'{self.movies_url}/possible-values-by-field'.replace(
            'v1.4', 'v1'
        )
        return self._perform_get_request(url, {'field': 'genres.name'})

    def get_movies_by_genres(
        self,
        genres: list | tuple,
        page: int = 1,
        limit: int = 10,
    ):
        """
        Получает пагинированный список фильмов по заданным жанрам.

        :param genres: Список названий жанров для фильтрации.
        :param page: Номер страницы.
        :param limit: Максимальное количество элементов на странице.
        """

        return self._get_filtered_movies(
            params={
                'genres.name': genres,
                'page': page,
                'limit': limit,
            },
            fields=('id', 'name'),
        )
