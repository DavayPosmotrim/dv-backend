from random import choice
from typing import Any, Optional

from custom_sessions.models import CustomSession
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from services.kinopoisk.kinopoisk_service import (KinopoiskCollections,
                                                  KinopoiskGenres)
from services.schemas import (collections_schema, genres_schema,
                              match_list_schema, movie_schema, roulette_schema,
                              session_schema, user_schema)
from services.utils import send_websocket_message
from users.models import User

from .serializers import (CollectionSerializer, CustomSessionCreateSerializer,
                          CustomUserSerializer, GenreSerializer,
                          MovieDetailSerializer, MovieSerializer)


class CreateUpdateUserView(APIView):
    """
    View to get, create and update user data.
    """

    @user_schema["get"]
    def get(self, request):
        device_id = request.headers.get("Device-Id")
        if device_id:
            user = get_object_or_404(User, device_id=device_id)
            serializer = CustomUserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            {"error_message": "Device-Id не был передан."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @user_schema["create"]
    def post(self, request):
        device_id = request.headers.get("Device-Id")
        print(device_id)
        print(request.headers)
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

    @user_schema["update"]
    def put(self, request):
        device_id = request.headers.get("Device-Id")
        if device_id:
            user = get_object_or_404(User, device_id=device_id)
            serializer = CustomUserSerializer(user, data=request.data)
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

    @genres_schema["get"]
    def get(self, request):
        kinopoisk_service = KinopoiskGenres()
        genres_data = kinopoisk_service.get_genres()
        if not genres_data:
            return Response(
                {"detail": "Ошибка получения жанров с Кинопоиска"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        serializer = GenreSerializer(genres_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CollectionListView(APIView):
    """Представление списка подборок."""

    @collections_schema["get"]
    def get(self, request):
        kinopoisk_service = KinopoiskCollections()
        collections_data = kinopoisk_service.get_collections()
        if not collections_data:
            return Response(
                {"detail": "Ошибка получения подборок с Кинопоиска"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        serializer = CollectionSerializer(collections_data["docs"], many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomSessionViewSet(viewsets.ModelViewSet):
    """Представление сессий ."""

    serializer_class = CustomSessionCreateSerializer
    queryset = CustomSession.objects.all()

    @session_schema["create"]
    def create(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Response:
        return super().create(request, *args, **kwargs)

    @session_schema["update"]
    def update(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Response:
        return super().update(request, *args, **kwargs)

    def perform_update(
        self, serializer: CustomSessionCreateSerializer
    ) -> None:
        session = serializer.save()
        self.update_session_image(session)

    def update_session_image(self, session: CustomSession) -> None:
        if session.status == 'closed':
            matched_movies = list(session.matched_movies)
            if matched_movies:
                top_movie = max(
                    matched_movies, key=lambda movie: movie.rating_kp
                )
                if top_movie and top_movie.poster:
                    session.image = top_movie.poster
                    session.save()

    @match_list_schema["get"]
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

    @roulette_schema["get"]
    @action(detail=True, methods=["get"])
    def get_roulette(self, request, pk=None):
        """Возвращает рандомный фильм
        если в списке совпадений более 2 фильмов или ошибку."""
        session = get_object_or_404(CustomSession, pk=pk)
        matched_movies = session.matched_movies
        if matched_movies.count() > 2:
            send_websocket_message(pk, "session_status", "roullete")
            random_movie = choice(matched_movies)
            random_movie_id = random_movie.id
            send_websocket_message(pk, "roulette", random_movie_id)
        else:
            error_message = "В списке совпадений должно быть более 2 фильмов."
            return Response(
                {"error_message": error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Представление списков и деталей фильмов.
    """

    serializer_class = MovieSerializer

    def get_queryset(self):
        session_id = self.kwargs.get("session_id")
        session = get_object_or_404(CustomSession, id=session_id)
        return session.movies

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return super().get_serializer_class()

    @movie_schema["get"]
    def retrieve(self, request, *args, **kwargs):
        try:
            movie_id = int(kwargs.get("pk"))  # Преобразуем строку в число
            queryset = self.get_queryset()
            movie = get_object_or_404(queryset, id=movie_id)
            serializer = self.get_serializer(movie)
            return Response(serializer.data)
        except ValueError:
            return Response({"error": "Некорректный movie ID"}, status=400)
