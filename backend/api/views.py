import logging
from random import choice
from typing import Any, Dict, Optional
from uuid import UUID

# import requests
from custom_sessions.models import CustomSession, CustomSessionMovieVote
# from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from movies.models import Collection, Genre, Movie
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
# from rest_framework.generics import CreateAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from services.kinopoisk.kinopoisk_service import (KinopoiskCollections,
                                                  KinopoiskGenres)
from services.schemas import device_id_header
from services.utils import close_session, send_websocket_message
from users.models import User

from .serializers import (CollectionSerializer, CreateVoteSerializer,
                          CustomSessionCreateSerializer,
                          CustomSessionListSerializer, CustomSessionSerializer,
                          CustomUserSerializer, GenreSerializer,
                          MovieReadDetailSerializer, MovieSerializer)

logger = logging.getLogger("views")


class CreateUpdateUserView(APIView):
    """
    View to get, create and update user data.
    """

    @extend_schema(parameters=[device_id_header])
    def get(self, request: Request) -> Response:
        device_id: Optional[str] = request.headers.get("Device-Id")
        if device_id:
            user: User = get_object_or_404(User, device_id=device_id)
            serializer = CustomUserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            {"error_message": "Device-Id не был передан."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        parameters=[device_id_header],
        request=CustomUserSerializer,
        responses=CustomUserSerializer,
    )
    def post(self, request: Request) -> Response:
        device_id: Optional[str] = request.headers.get("Device-Id")
        if device_id:
            serializer = CustomUserSerializer(
                data=request.data,
                context={"device_id": device_id}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {"error_message": "Device-Id не был передан."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        parameters=[device_id_header],
        request=CustomUserSerializer,
        responses=CustomUserSerializer,
    )
    def put(self, request: Request) -> Response:
        device_id: Optional[str] = request.headers.get("Device-Id")
        if device_id:
            user = get_object_or_404(User, device_id=device_id)
            serializer = CustomUserSerializer(
                user,
                data=request.data,
                partial=True,
                context={"device_id": device_id},
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {"error_message": "Device-Id не был передан."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class GenreListView(APIView):
    """Представление списка жанров."""

    @extend_schema(parameters=[device_id_header])
    def get(self, request: Request) -> Response:
        genres = Genre.objects.all()
        if genres.exists():
            serializer = GenreSerializer(genres, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        # Если база пуста, получаем жанры с API кинопоиск
        kinopoisk_service = KinopoiskGenres()
        genres_data: Optional[Any] = kinopoisk_service.get_genres()
        if not genres_data:
            return Response(
                {"detail": "Ошибка получения жанров с Кинопоиска"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        # сохраняем объекты в базу данных
        for genre_data in genres_data:
            Genre.objects.create(name=genre_data['name'])
        serializer = GenreSerializer(genres_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CollectionListView(APIView):
    """Представление списка подборок."""

    @extend_schema(parameters=[device_id_header])
    def get(self, request: Request) -> Response:
        collections = Collection.objects.all()
        if collections.exists():
            serializer = CollectionSerializer(collections, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        # Если база пуста, получаем подборки с API кинопоиск
        kinopoisk_service = KinopoiskCollections()
        collections_data = kinopoisk_service.get_collections()
        if not collections_data:
            return Response(
                {"detail": "Ошибка получения подборок с Кинопоиска"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        # сохраняем объекты в базу данных
        for collection_data in collections_data.get('docs', []):
            cover = collection_data.get('cover', {}).get('url')
            logger.info(f"Получен cover URL: {cover}")

            collection = Collection(
                slug=collection_data.get('slug'),
                name=collection_data.get('name'),
                cover=cover if cover else None
            )
            collection.save()

        # Обновляем queryset после добавления новых объектов
        collections = Collection.objects.all()
        serializer = CollectionSerializer(collections, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomSessionCreateView(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    """Представление для создания новой сессии."""

    serializer_class = CustomSessionCreateSerializer
    queryset = CustomSession.objects.all()

    @extend_schema(parameters=[device_id_header])
    def create(self, request: Request, *args: Any, **kwargs: Any
               ) -> Response:

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CustomSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для просмотра сессий и дополительных действий."""

    def get_queryset(self):
        """Возвращает queryset, отфильтрованный по device_id."""
        device_id = self.request.headers.get("Device-Id")
        if not device_id:
            return CustomSession.objects.none()
        return CustomSession.objects.filter(users__device_id=device_id)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            session_id = self.kwargs.get("pk")
            session = get_object_or_404(
                CustomSession, id=session_id
            )
            if session.status == "closed":
                return CustomSessionSerializer
            return CustomSessionCreateSerializer
        else:
            return CustomSessionListSerializer

    @extend_schema(parameters=[device_id_header])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(parameters=[device_id_header])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(parameters=[device_id_header], request=None)
    @action(detail=True,
            methods=["post", "delete"],
            url_path="connection")
    def get_connection(
        self, request: Request, pk: Optional[int] = None
    ) -> Response:
        """Метод для добавления и удаления пользователь в сессии:
        - POST - для добавления пользователя,
        - DELETE - для удаления пользователя."""
        user_id = request.headers.get("Device-Id")
        user = get_object_or_404(User, pk=user_id)
        session = get_object_or_404(CustomSession, pk=pk)
        user_ids = session.users.values_list("device_id", flat=True)
        user_uuid = UUID(user_id)
        if request.method == "POST":
            if user_uuid in user_ids:
                error_message = "Вы уже подключены к этому сеансу."
            elif session.status == "waiting":
                session.users.add(user)
                session.save()
                serializer = CustomUserSerializer(session.users, many=True)
                send_websocket_message(pk, "users", serializer.data)
                message = f"Вы присоединились к сеансу {pk}"
                return Response({"message": message},
                                status=status.HTTP_201_CREATED)
            else:
                error_message = "К этому сеансу нельзя подключиться."
            return Response(
                {"error_message": error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # close session if user disconnects during the voting stage
        # and broadcast the message to other users in the session
        logger.debug(f"start user disconnect {user_uuid=}, {user_ids=}")
        if user_uuid not in user_ids:
            error_message = "Вы не являетесь участником данного сеанса."
            return Response(
                {"error_message": error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if session.status == "voting":
            close_session(session, pk)
            return Response({"message": "Сеанс закрыт."},
                            status=status.HTTP_200_OK)
        # code for delete method
        session.users.remove(user)
        session.save()
        serializer = CustomUserSerializer(session.users, many=True)
        send_websocket_message(pk, "users", serializer.data)
        return Response({"message": f"Вы покинули сеанс {pk}"},
                        status=status.HTTP_200_OK)

    @extend_schema(parameters=[device_id_header], request=None)
    @action(detail=True,
            methods=["get"],
            url_path="start_voting")
    def get_start_voting(
        self, request: Request, pk: Optional[int] = None
    ) -> Response:
        """Меняет статус сессии на voting
        и отправляет сообщение о изменении на вебсокет."""
        session = get_object_or_404(CustomSession, pk=pk)
        if session.status != "waiting":
            error_message = "Эту сессию нельзя перевести в режим голосования"
            return Response(
                {"error_message": error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        if session.users.count() < 2:
            return Response(
                {"error_message": "Участников должно быть 2 и более"},
                status=status.HTTP_400_BAD_REQUEST
            )
        new_status = "voting"
        session.status = new_status
        session.save()
        send_websocket_message(pk, "session_status", new_status)
        return Response({"message": "Вы начали сеанс"},
                        status=status.HTTP_200_OK)

    @extend_schema(parameters=[device_id_header])
    @action(detail=True, methods=["get"])
    def get_matched_movies(
        self, request: Request, pk: Optional[int] = None
    ) -> Response:
        """Возвращает фильмы, за которые проголосовали все пользователи
        в сесиии (мэтчи) - или ошибку, если мэтчей нет ."""
        session = get_object_or_404(CustomSession, pk=pk)
        matched_movies = session.matched_movies
        if matched_movies:
            serializer = MovieSerializer(matched_movies, many=True)
            return Response(serializer.data)
        else:
            return Response({"message": "Нет ни одного совпадения"})

    @extend_schema(parameters=[device_id_header])
    @action(detail=True, methods=["get"])
    def get_roulette(
        self, request: Request, pk: Optional[str] = None
    ) -> Response:
        """Возвращает рандомный фильм
        если в списке совпадений более 2 фильмов или ошибку."""
        session = get_object_or_404(CustomSession, pk=pk)
        matched_movies = session.matched_movies.all()
        if matched_movies.count() > 2:
            send_websocket_message(pk, "session_status", "roulette")
            random_movie = choice(list(matched_movies))
            random_movie_id = random_movie.id
            send_websocket_message(pk, "roulette", random_movie_id)
            close_session(session, pk)
            return Response(
                {"random_movie_id": random_movie_id},
                status=status.HTTP_200_OK
            )
        else:
            error_message = "В списке совпадений должно быть более 2 фильмов."
            return Response(
                {"error_message": error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MovieViewSet(ListModelMixin, GenericViewSet):
    """
    Представление набора фильмов в сессии для голосования.
    """

    serializer_class = MovieSerializer

    def get_queryset(self):
        session_id = self.kwargs.get("session_id")
        session = get_object_or_404(CustomSession, id=session_id)
        return session.movies

    @extend_schema(parameters=[device_id_header], request=None)
    @action(detail=True,
            methods=["post", "delete"],
            url_path="like")
    def like(self, request: Request, *args, **kwargs) -> Response:
        """
        Метод для добавления и удаления лайков:
        - POST - добавляет лайк,
        - DELETE - удаляет лайк.
        """
        user_id = request.headers.get("Device-Id")
        session_id = kwargs.get("session_id")
        movie_id = int(kwargs.get("pk"))
        session = get_object_or_404(CustomSession, pk=session_id)
        # Проверка статуса сессии
        if session.status != "voting":
            error_message = "Сессия должна быть в статусе voting."
            return Response({"error_message": error_message},
                            status=status.HTTP_400_BAD_REQUEST)
        user_ids = session.users.values_list("device_id", flat=True)
        movie_ids = session.movies.values_list("id", flat=True)
        user_uuid = UUID(user_id)
        if movie_id in session.matched_movies.values_list("id", flat=True):
            error_message = "Этот фильм уже находится в совпадениях."
            return Response({"error_message": error_message},
                            status=status.HTTP_400_BAD_REQUEST)
        if user_uuid not in user_ids:
            # if user_id not in user_ids:
            error_message = ("Этот пользователь не может "
                             "принимать участие в голосовании.")
            return Response(
                {"error_message": error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        if movie_id not in movie_ids:
            error_message = "Этого фильма нет в списке для голосования."
            return Response({"error_message": error_message},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == "POST":
            serializer = CreateVoteSerializer(data={
                "user_id": user_id,
                "session_id": session_id,
                "movie_id": movie_id
            })
            if serializer.is_valid():
                serializer.save()
                if user_ids.count() == CustomSessionMovieVote.objects.filter(
                    movie_id=movie_id,
                    session_id=session_id
                ).count():
                    send_websocket_message(session_id, "matches", movie_id)
                    movie = get_object_or_404(Movie, pk=movie_id)
                    session.matched_movies.add(movie)
                    session.save()
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        # code for delete method
        vote = CustomSessionMovieVote.objects.filter(
            user_id=user_id,
            session_id=session_id,
            movie_id=movie_id
        ).first()
        if vote:
            vote.delete()
            return Response({"message": "Голос удален."},
                            status=status.HTTP_200_OK)
        return Response({"message": "Вы еще не проголосовали за этот фильм."},
                        status=status.HTTP_404_NOT_FOUND)


class MovieDetailView(APIView):
    """
    Представление для получения детальной информации о фильме.
    """

    @extend_schema(parameters=[device_id_header])
    def get(
        self, request: Request, *args: Any, **kwargs: Dict[str, Any]
    ) -> Response:
        movie_id = self.kwargs.get("id")
        movie = get_object_or_404(Movie, id=movie_id)
        serializer = MovieReadDetailSerializer(movie)
        return Response(serializer.data, status=status.HTTP_200_OK)
