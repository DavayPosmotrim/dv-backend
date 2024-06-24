from api.serializers import (CustomUserSerializer, MovieDetailSerializer,
                             MovieSerializer)
from drf_spectacular.utils import (OpenApiParameter, OpenApiResponse,
                                   extend_schema)

user_schema = {
    'get': extend_schema(
        summary='Получение данных пользователя',
        description='Возвращает данные пользователя по указанному device_id',
        methods=['GET'],
        parameters=[
            OpenApiParameter(
                name='device_id',
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
            )
        ],
        responses={
            200: CustomUserSerializer,
            400: OpenApiResponse(description='Bad Request'),
        }
    ),
    'create': extend_schema(
        summary='Создание пользователя',
        description='Создает нового пользователя',
        methods=['POST'],
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
        parameters=[
            OpenApiParameter(
                name='device_id',
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
            )
        ],
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
