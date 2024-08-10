from random import choice
from typing import Any, Dict, Optional

from custom_sessions.models import CustomSession, CustomSessionMovieVote
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from services.kinopoisk.kinopoisk_service import (KinopoiskCollections,
                                                  KinopoiskGenres)
from services.schemas import (collections_schema, genres_schema,
                              match_list_schema, movie_schema, roulette_schema,
                              session_schema, user_schema)
from services.utils import close_session, send_websocket_message
from users.models import User

from .serializers import (CollectionSerializer, CreateVoteSerializer,
                          CustomSessionCreateSerializer, CustomUserSerializer,
                          GenreSerializer, MovieReadDetailSerializer,
                          MovieSerializer)
from movies.models import Movie


class CreateUpdateUserView(APIView):
    """
    View to get, create and update user data.
    """

    @user_schema["get"]
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

    @user_schema["create"]
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

    @user_schema["update"]
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

    @genres_schema["get"]
    def get(self, request: Request) -> Response:
        kinopoisk_service = KinopoiskGenres()
        genres_data: Optional[Any] = kinopoisk_service.get_genres()
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
    def get(self, request: Request) -> Response:
        kinopoisk_service = KinopoiskCollections()
        collections_data: Optional[dict[str, Any]] = (
            kinopoisk_service.get_collections()
        )
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
    def get_roulette(
        self, request: Request, pk: Optional[str] = None
    ) -> Response:
        """Возвращает рандомный фильм
        если в списке совпадений более 2 фильмов или ошибку."""
        session = get_object_or_404(CustomSession, pk=pk)
        matched_movies = session.matched_movies
        if matched_movies.count() > 2:
            send_websocket_message(pk, "session_status", "roulette")
            random_movie = choice(matched_movies)
            random_movie_id = random_movie.id
            send_websocket_message(pk, "roulette", random_movie_id)
            close_session(session, pk)
        else:
            error_message = "В списке совпадений должно быть более 2 фильмов."
            return Response(
                {"error_message": error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True,
            methods=["post", "delete"],
            url_path="connection")
    def get_connection(
        self, request: Request, pk: Optional[int] = None
    ) -> Response:
        user_id = request.headers.get("Device-Id")
        user = get_object_or_404(User, pk=user_id)
        session = get_object_or_404(CustomSession, pk=pk)
        user_ids = session.users.values_list("id", flat=True)
        if request.method == "POST":
            if user_id in user_ids:
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
        if user_id not in user_ids:
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
                        status=status.HTTP_204_NO_CONTENT)


class MovieViewSet(ListModelMixin, GenericViewSet):
    """
    Представление набора фильмов в сессии для голосования.
    """

    serializer_class = MovieSerializer

    def get_queryset(self):
        session_id = self.kwargs.get("session_id")
        session = get_object_or_404(CustomSession, id=session_id)
        return session.movies

    @action(detail=True,
            methods=["post", "delete"],
            url_path="like")
    def like(self, request: Request, pk: Optional[int] = None) -> Response:
        user_id = request.headers.get("Device-Id")
        session_id = self.kwargs.get("session_id")
        movie_id = pk
        session = get_object_or_404(CustomSession, pk=session_id)
        user_ids = session.users.values_list("id", flat=True)
        if movie_id in session.matched_movies.values_list("id", flat=True):
            error_message = "Этот фильм уже находится в совпадениях."
            return Response({"error_message": error_message},
                            status=status.HTTP_400_BAD_REQUEST)
        if user_id not in user_ids:
            error_message = ("Этот пользователь не может "
                             "принимать участия в голосвании.")
            return Response(
                {"error_message": error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        if movie_id not in session.movies.values_list("id", flat=True):
            error_message = "Этого фильма нет в списке для голования."
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
                    session.matched_movies.add(movie_id)
                    session.save()
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(serializer.error,
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
                            status=status.HTTP_204_NO_CONTENT)
        return Response({"message": "Вы еще не проголосовали за этот фильм."},
                        status=status.HTTP_204_NO_CONTENT)


class MovieDetailView(APIView):
    """
    Представление для получения детальной информации о фильме.
    """

    @movie_schema["get"]
    def get(
        self, request: Request, *args: Any, **kwargs: Dict[str, Any]
    ) -> Response:
        movie_id = self.kwargs.get("movie_id")
        movie = get_object_or_404(Movie, id=movie_id)
        serializer = MovieReadDetailSerializer(movie)
        return Response(serializer.data, status=status.HTTP_200_OK)
