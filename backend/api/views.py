from random import choice

from custom_sessions.models import CustomSession
from django.shortcuts import get_object_or_404
from movies.models import Movie
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from services.kinopoisk.kinopoisk_service import (KinopoiskCollections,
                                                  KinopoiskGenres)
from services.schemas import (match_list_schema, movie_detail_schema,
                              session_schema, user_schema)
from users.models import User

from .serializers import (CollectionSerializer, CustomSessionCreateSerializer,
                          CustomUserSerializer, GenreSerializer,
                          MovieDetailSerializer, MovieSerializer)


class CreateUpdateUserView(APIView):
    """
    View to get, create and update user data.
    """

    @user_schema['get']
    def get(self, request):
        device_id = request.headers.get('Device-Id')
        if device_id:
            user = get_object_or_404(User, device_id=device_id)
            serializer = CustomUserSerializer(user)
            return Response(serializer.data,
                            status=status.HTTP_200_OK)
        return Response({'error_message': 'Device-Id не был передан.'},
                        status=status.HTTP_400_BAD_REQUEST)

    @user_schema['create']
    def post(self, request):
        device_id = request.headers.get('Device-Id')
        print(device_id)
        print(request.headers)
        if device_id:
            serializer = CustomUserSerializer(
                data=request.data,
                context={'device_id': device_id}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({'error_message': 'Device-Id не был передан.'},
                        status=status.HTTP_400_BAD_REQUEST)

    @user_schema['update']
    def put(self, request):
        device_id = request.headers.get('Device-Id')
        if device_id:
            user = get_object_or_404(User, device_id=device_id)
            serializer = CustomUserSerializer(
                user,
                data=request.data
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({'error_message': 'Device-Id не был передан.'},
                        status=status.HTTP_400_BAD_REQUEST)


class GenreListView(APIView):
    """Представление списка жанров."""

    def get(self, request):
        kinopoisk_service = KinopoiskGenres()
        genres_data = kinopoisk_service.get_genres()
        if not genres_data:
            return Response(
                {"detail": "Ошибка получения жанров с Кинопоиска"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        serializer = GenreSerializer(genres_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CollectionListView(APIView):
    """Представление списка подборок."""

    def get(self, request):
        kinopoisk_service = KinopoiskCollections()
        collections_data = kinopoisk_service.get_collections()
        if not collections_data:
            return Response(
                {"detail": "Ошибка получения подборок с Кинопоиска"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        serializer = CollectionSerializer(collections_data['docs'], many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomSessionViewSet(viewsets.ModelViewSet):
    """Представление сессий ."""

    serializer_class = CustomSessionCreateSerializer
    queryset = CustomSession.objects.all()

    @session_schema['create']
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @match_list_schema['get']
    @action(detail=True, methods=['get'])
    def get_matched_movies(self, request, pk=None):
        """Возвращает фильмы, за которые проголосовали все пользователи
        в сесиии (мэтчи) - или ошибку, если мэтчей нет ."""
        session = get_object_or_404(CustomSession, pk=pk)
        matched_movies = session.matched_movies
        if matched_movies:
            serializer = MovieSerializer(matched_movies, many=True)
            return Response(serializer.data)
        else:
            return Response({"message": "Нет ни одного совпадения"})

    @action(detail=False, methods=['get'])
    def get_roulette(self):
        """Возвращает рандомный фильм
        если в списке совпадений более 2 фильмов или ошибку."""
        matched_movies = self.get_matched_movies()
        if matched_movies.count() > 2:
            random_movie = choice(matched_movies)
            serializer = MovieSerializer(random_movie)
            return Response(serializer.data)
        return Response(
            {'error_message': (
                'В списке совпадений '
                'должно быть более 2 фильмов.')},
            status=status.HTTP_400_BAD_REQUEST
        )


class MovieListView(generics.ListAPIView):
    """Представление списка фильмов."""

    serializer_class = MovieSerializer

    def get_queryset(self):
        session_id = self.kwargs.get('session_id')
        session = get_object_or_404(CustomSession, id=session_id)
        return session.movies


class MovieDetailView(APIView):
    """Представление для получения деталей конкретного фильма."""

    @movie_detail_schema['get']
    def get(self, request, session_id, movie_id):
        session = get_object_or_404(CustomSession, id=session_id)
        movie = get_object_or_404(Movie, id=movie_id, custom_sessions=session)
        serializer = MovieDetailSerializer(movie)
        return Response(serializer.data)
