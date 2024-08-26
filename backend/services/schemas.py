from api.serializers import (CollectionSerializer,
                             CreateVoteSerializer,
                             CustomSessionCreateSerializer,
                             CustomUserSerializer, GenreSerializer,
                             MovieReadDetailSerializer,
                             MovieRouletteSerializer, MovieSerializer)

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiParameter, OpenApiResponse,
                                   extend_schema)

device_id_header = OpenApiParameter(
    name="Device-Id",
    type=str,
    location=OpenApiParameter.HEADER,
    required=True,
    description="Device-Id пользователя",
)


user_schema = {
    "get": extend_schema(
        summary="Получение данных пользователя",
        description="Возвращает данные пользователя по указанному device_id",
        methods=["GET"],
        parameters=[device_id_header],
        responses={
            200: CustomUserSerializer,
            400: OpenApiResponse(description="Bad Request"),
        },
    ),
    "create": extend_schema(
        summary="Создание пользователя",
        description="Создает нового пользователя",
        methods=["POST"],
        parameters=[device_id_header],
        request=CustomUserSerializer,
        responses={
            201: CustomUserSerializer,
            400: OpenApiResponse(description="Bad Request"),
        },
    ),
    "update": extend_schema(
        summary="Обновление данных пользователя",
        description="Обновляет данные существующего пользователя по device_id",
        methods=["PUT"],
        parameters=[device_id_header],
        request=CustomUserSerializer,
        responses={
            200: CustomUserSerializer,
            400: OpenApiResponse(description="Bad Request"),
        },
    ),
}

match_list_schema = {
    "get": extend_schema(
        summary="Мэтчи в сесиии",
        description=(
            "Возвращает список фильмов, "
            "которые пользователи отметили как совпадения"
        ),
        methods=["GET"],
        responses={
            200: MovieSerializer(many=True),
            404: OpenApiResponse(
                description="Совпадений не нашлось, добавтье больше фильмов"
            ),
        },
    )
}

session_schema = {
    "get": extend_schema(
        summary="Получение данных сессии текущего пользователя",
        description="Возвращает данные сессии",
        methods=["GET"],
        parameters=[device_id_header],
        responses={
            200: CustomSessionCreateSerializer,
            400: OpenApiResponse(description="Bad Request"),
        },
    ),
    "create": extend_schema(
        summary="Создание сессии",
        description="Создает новую сессию",
        methods=["POST"],
        parameters=[device_id_header],
        request=CustomSessionCreateSerializer,
        responses={
            201: CustomSessionCreateSerializer,
            400: OpenApiResponse(description="Bad Request"),
        },
    ),
    "update": extend_schema(
        summary="Обновление данных сессии",
        description="Обновляет данные сессии",
        methods=["PATCH"],
        parameters=[device_id_header],
        request=CustomSessionCreateSerializer,
        responses={
            201: CustomSessionCreateSerializer,
            400: OpenApiResponse(description="Bad Request"),
        },
    ),
}

genres_schema = {
    "get": extend_schema(
        summary="Получение списка жанров",
        description=("Возвращает список всех жанров"),
        methods=["GET"],
        responses={
            200: GenreSerializer(many=True),
            400: OpenApiResponse(description="Bad Request"),
        },
    )
}

collections_schema = {
    "get": extend_schema(
        summary="Получение списка подборок",
        description=("Возвращает список всех подборок с Кинопоиска"),
        methods=["GET"],
        responses={
            200: CollectionSerializer(many=True),
            400: OpenApiResponse(description="Bad Request"),
        },
    )
}

roulette_schema = {
    "get": extend_schema(
        summary="Рулетка",
        description=("Возвращает случайный фильм из мэтчей"),
        methods=["GET"],
        responses={
            200: MovieRouletteSerializer(many=True),
            400: OpenApiResponse(description="Bad Request"),
        },
    )
}

movie_schema = {
    "get": extend_schema(
        summary="Подробнее о фильме",
        description=("Возвращает детали конкретного фильма"),
        methods=["GET"],
        responses={
            200: MovieReadDetailSerializer(many=True),
            400: OpenApiResponse(description="Bad Request"),
        },
        parameters=[
            OpenApiParameter(
                name="movie_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID фильма",
            )
        ],
    )
}

like_schema = {
    "create": extend_schema(
        summary="Лайк к фильму",
        description="Создает голос за фильм из списка фильмов текущей сессии",
        methods=["POST"],
        parameters=[
            OpenApiParameter(
                name='session_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH
            ),
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH
            ),
            device_id_header
        ],
        responses={
            201: CreateVoteSerializer,
            400: OpenApiResponse(description="Bad Request"),
        },
    ),
    "delete": extend_schema(
        summary="Удаление лайка к фильму",
        description="Удаляет голос за фильм из списка фильмов текущей сессии",
        methods=["DELETE"],
        parameters=[
            OpenApiParameter(
                name='session_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH
            ),
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH
            ),
            device_id_header
        ],
        responses={
            204: OpenApiResponse(description="No Content"),
            400: OpenApiResponse(description="Bad Request"),
            404: OpenApiResponse(description="Vote Not Found"),
        },
    ),
}

connection_schema = {
    "create": extend_schema(
        summary="Подключение пользователей к сессии",
        description="Добавляет юзеров в базу данных в модель сессии",
        methods=["POST"],
        parameters=[device_id_header],
        responses={
            201: CustomSessionCreateSerializer,
            400: OpenApiResponse(description="Bad Request"),
        },
    ),
    "delete": extend_schema(
        summary="Отключение пользователей от сессии",
        description="Удаляет юзера из объекта сессии",
        methods=["DELETE"],
        parameters=[device_id_header],
        responses={
            204: OpenApiResponse(description="No Content"),
            400: OpenApiResponse(description="Bad Request"),
        },
    ),
}
