from random import choice

from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from custom_sessions.models import CustomSession
from movies.models import Genre, Movie
from services.schemas import (
    match_list_schema, user_schema)
from users.models import User
from .serializers import (CustomSessionCreateSerializer, CustomUserSerializer,
                          GenreSerializer, MovieSerializer,
                          MovieDetailSerializer)


class CreateUpdateUserView(APIView):
    """
    View to get, create and update user data.
    """

    @user_schema['get']
    def get(self, request, *args, **kwargs):
        device_id = kwargs.get('device_id', False)
        if device_id:
            user = get_object_or_404(User, device_id=device_id)
            serializer = CustomUserSerializer(user)
            return Response(serializer.data,
                            status=status.HTTP_200_OK)
        return Response({'error_message': 'Device id не был передан.'},
                        status=status.HTTP_400_BAD_REQUEST)

    @user_schema['create']
    def post(self, request, *args, **kwargs):
        device_id = kwargs.get('device_id', False)
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
        return Response({'error_message': 'Device id не был передан.'},
                        status=status.HTTP_400_BAD_REQUEST)

    @user_schema['update']
    def put(self, request, *args, **kwargs):
        device_id = kwargs.get('device_id', False)
        if device_id:
            user = get_object_or_404(User, device_id=device_id)
            serializer = CustomUserSerializer(
                user,
                data=request.data,
                context={'device_id': device_id}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({'error_message': 'Device id не был передан.'},
                        status=status.HTTP_400_BAD_REQUEST)


class GenreListView(generics.ListAPIView):
    """Представление списка жанров."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class CustomSessionViewSet(viewsets.ModelViewSet):
    """Представление сессий ."""

    serializer_class = CustomSessionCreateSerializer

    def get_queryset(self):
        device_id = self.request.headers.get('device_id')
        if device_id:
            try:
                return CustomSession.objects.filter(
                    users__device_id=device_id
                )
            except CustomSession.DoesNotExist:
                return Response({"message": "У вас еще нет сессий"})
        else:
            return Response({"message": "Требуется device_id"})

    def create(self, request, *args, **kwargs):
        # print(request.headers)
        # device_id = request.headers.get('device_id')
        # if not device_id:
        #     return Response(
        #         {"message": "Требуется device_id"},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )

        # try:
        #     user = User.objects.get(device_id=device_id)
        # except User.DoesNotExist:
        #     return Response(
        #         {"message": "Пользователь с указанным device_id не найден"},
        #         status=status.HTTP_404_NOT_FOUND
        #     )

        genres = request.data.get('genres', [])
        collections = request.data.get('collections', [])

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.context.update({
            'genres': genres,
            'collections': collections
        })
        self.perform_create(serializer)
        # serializer.save(users=[user])
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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

    def get(self, request, movie_id):
        movie = get_object_or_404(Movie, id=movie_id)
        serializer = MovieDetailSerializer(movie)
        return Response(serializer.data)
