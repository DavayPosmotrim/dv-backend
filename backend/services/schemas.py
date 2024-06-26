from api.serializers import (CollectionSerializer,
                             CustomSessionCreateSerializer,
                             CustomUserSerializer, GenreSerializer,
                             MovieDetailSerializer, MovieRouletteSerializer,
                             MovieSerializer)
from drf_spectacular.utils import (OpenApiParameter, OpenApiResponse,
                                   extend_schema)

device_id_header = OpenApiParameter(
    name='Device-Id',
    type=str,
    location=OpenApiParameter.HEADER,
    required=True,
    description='Device-Id пользователя'
)


user_schema = {
    'get': extend_schema(
        summary='Получение данных пользователя',
        description='Возвращает данные пользователя по указанному device_id',
        methods=['GET'],
        parameters=[device_id_header],
        responses={
            200: CustomUserSerializer,
            400: OpenApiResponse(description='Bad Request'),
        }
    ),
    'create': extend_schema(
        summary='Создание пользователя',
        description='Создает нового пользователя',
        methods=['POST'],
        parameters=[device_id_header],
        request=CustomUserSerializer,
        responses={
            201: CustomUserSerializer,
            400: OpenApiResponse(description='Bad Request'),
        }
    ),
    'update': extend_schema(
        summary='Обновление данных пользователя',
        description='Обновляет данные существующего пользователя по device_id',
        methods=['PUT'],
        parameters=[device_id_header],
        request=CustomUserSerializer,
        responses={
            200: CustomUserSerializer,
            400: OpenApiResponse(description='Bad Request'),
        }
    ),
}

match_list_schema = {
    'get': extend_schema(
        summary='Получение списка избранных фильмов',
        description=(
            'Возвращает список фильмов, '
            'которые пользователи отметили как совпадения'
        ),
        methods=['GET'],
        responses={
            200: MovieSerializer(many=True),
            404: OpenApiResponse(
                description='Совпадений не нашлось, добавтье больше фильмов'),
        }
    )
}

movie_detail_schema = {
    'get': extend_schema(
        summary='Получение подробной информации о фильме',
        description=(
            'Возвращает объект фильма '
            'содержит данные: уникальный номер, название, описание,'
            'постер, год, страны, оригинальное название, рейтинг, длительность'
            'жанры, персоны (актеры, режиссеры)'
        ),
        methods=['GET'],
        responses={
            200: MovieDetailSerializer,
            404: OpenApiResponse(
                description='Фильм отсутствует в базе данных'),
        }
    )
}

session_schema = {
    'get': extend_schema(
        summary='Получение данных сессии текущего пользователя',
        description='Возвращает данные сессии',
        methods=['GET'],
        parameters=[device_id_header],
        responses={
            200: CustomSessionCreateSerializer,
            400: OpenApiResponse(description='Bad Request'),
        }
    ),
    'create': extend_schema(
        summary='Создание сессии',
        description='Создает новую сессию',
        methods=['POST'],
        parameters=[device_id_header],
        request=CustomSessionCreateSerializer,
        responses={
            201: CustomSessionCreateSerializer,
            400: OpenApiResponse(description='Bad Request'),
        }
    ),
}

genres_schema = {
    'get': extend_schema(
        summary='Получение списка жанров',
        description=(
            'Возвращает список всех жанров'
        ),
        methods=['GET'],
        responses={
            200: GenreSerializer(many=True),
            400: OpenApiResponse(description='Bad Request'),
        }
    )
}

collections_schema = {
    'get': extend_schema(
        summary='Получение списка подборок',
        description=(
            'Возвращает список всех подборок с Кинопоиска'
        ),
        methods=['GET'],
        responses={
            200: CollectionSerializer(many=True),
            400: OpenApiResponse(description='Bad Request'),
        }
    )
}

roulette_schema = {
    'get': extend_schema(
        summary='Рулетка',
        description=(
            'Возвращает случайный фильм из мэтчей'
        ),
        methods=['GET'],
        responses={
            200: MovieRouletteSerializer(many=True),
            400: OpenApiResponse(description='Bad Request'),
        }
    )
}
