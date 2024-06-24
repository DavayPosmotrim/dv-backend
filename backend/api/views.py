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
from services.schemas import match_list_schema, movie_detail_schema

from .serializers import (CollectionSerializer,  # GenreSerializer,
                          CustomSessionCreateSerializer, GenreSerializer,
                          MovieDetailSerializer, MovieSerializer)

# class GenreListView(generics.ListAPIView):
#     """Представление списка жанров."""

#     queryset = Genre.objects.all()
#     serializer_class = GenreSerializer


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

    # def get_queryset(self):
    #     device_id = self.request.headers.get('device_id')
    #     if device_id:
    #         try:
    #             return CustomSession.objects.filter(
    #                 users__device_id=device_id
    #             )
    #         except CustomSession.DoesNotExist:
    #             return Response({"message": "У вас еще нет сессий"})
    #     else:
    #         return Response({"message": "Требуется device_id"})

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

    queryset = Movie.objects.all()
    serializer_class = MovieSerializer


class MovieDetailView(APIView):
    """Представление для получения деталей конкретного фильма."""

    @movie_detail_schema['get']
    def get(self, request, movie_id):
        movie = get_object_or_404(Movie, id=movie_id)
        serializer = MovieDetailSerializer(movie)
        return Response(serializer.data)
