from random import choice

from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from custom_sessions.models import CustomSession
from movies.models import Genre, Movie
from services.schemas import (
    user_schema, user_session_list_schema)
from users.models import User

from .serializers import (
                          CustomSessionCreateSerializer, CustomUserSerializer,
                          GenreSerializer, MovieSerializer,
                          )


class CreateUpdateUserView(APIView):
    """
    View to get, create and update user data.
    """

    @user_schema['get']
    def get(self, request):
        device_id = request.data.get('device_id', False)
        if device_id:
            user = get_object_or_404(User, device_id=device_id)
            serializer = CustomUserSerializer(user)
            return Response(serializer.data,
                            status=status.HTTP_200_OK)
        return Response({'error_message': 'Device id не был передан.'},
                        status=status.HTTP_400_BAD_REQUEST)

    @user_schema['create']
    def post(self, request):
        serializer = CustomUserSerializer(
            data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    @user_schema['update']
    def put(self, request):
        device_id = request.data.get('device_id', False)
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
        return Response({'error_message': 'Device id не был передан.'},
                        status=status.HTTP_400_BAD_REQUEST)


class GenreListView(generics.ListAPIView):
    """Представление списка жанров."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class CustomSessionViewSet(viewsets.ModelViewSet):
    """Представление текущей сессии для пользователя
    и списка закрытых сессий пользователя
    с возможностью посмотреть их детали."""

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

    @action(detail=True, methods=['get'])
    def matched_movies(self, request, pk=None, *args, **kwargs):
        """Возвращает фильмы, за которые проголосовали все пользователи
        в сесиии (мэтчи) - или ошибку, если мэтчей нет ."""
        matched_movies = self.matched_movies()
        if matched_movies:
            serializer = MovieSerializer(matched_movies, many=True)
            return Response(serializer.data)
        else:
            return Response({"message": "Нет ни одного совпадения"})

    @action(detail=False, methods=['get'])
    def get_roulette(self):
        """Возвращает рандомный фильм
        если в списке совпадений более 2 фильмов или ошибку."""
        matched_movies = self.matched_movies()
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
