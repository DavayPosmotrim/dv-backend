from api.serializers import (
    CustomSessionSerializer, CustomUserSerializer, MovieSerializer)
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
            'которые пользователь отметил как совпадения'
        ),
        methods=['GET'],
        responses={
            200: MovieSerializer(many=True),
            404: OpenApiResponse(
                description='Совпадений не нашлось, добавтье больше фильмов'),
        }
    )
}

user_session_list_schema = {
    'get': extend_schema(
        summary='Получение списка сессий пользователя',
        description=(
            'Возвращает список сессий текущего пользователя. '
        ),
        methods=['GET'],
        responses={
            200: CustomSessionSerializer(many=True),
            404: OpenApiResponse(
                description='У вас нет ни одной сессии'),
        }
    )
}
