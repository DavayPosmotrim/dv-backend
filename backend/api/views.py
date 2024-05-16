
from random import choice

from custom_sessions.models import CustomSession
from django.shortcuts import get_object_or_404
from movies.models import Genre, Movie
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import User

from .serializers import (CustomSessionSerializer, CustomUserSerializer,
                          GenreSerializer, MovieSerializer)


class CreateUpdateUserView(APIView):
    """
    View to get, create and update user data.
    """
    def get(self, request, *args, **kwargs):
        device_id = kwargs.get('device_id', False)
        if device_id:
            user = get_object_or_404(User, device_id=device_id)
            serializer = CustomUserSerializer(user)
            return Response(serializer.data,
                            status=status.HTTP_200_OK)
        return Response({'error_message': 'Device id не был передан.'},
                        status=status.HTTP_400_BAD_REQUEST)

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


class GenreListView(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Представление списка жанров."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class CustomSessionCreateView(generics.CreateAPIView):
    """Создание пользовательского сеанса."""

    queryset = CustomSession.objects.all()
    serializer_class = CustomSessionSerializer


class UserSessionListView(generics.ListAPIView):
    """Представление списка сеансов пользователя."""

    serializer_class = CustomSessionSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return CustomSession.objects.filter(users__id=user_id)


class MovieListView(generics.ListAPIView):
    """Представление списка фильмов."""

    queryset = Movie.objects.all()
    serializer_class = MovieSerializer


class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Представление списка избранных фильмов (совпадений).
    Функционал рулетки - рандомный выбор фильма из списка совподений.
    """

    serializer_class = MovieSerializer

    def get_queryset(self):
        session_id = self.request.session.get('session_id')
        if session_id:
            session = CustomSession.objects.get(id=session_id)
            return session.movies.filter(matched=True)
        return Movie.objects.none()

    @action(detail=False,
            method=['get'],
            url_path='roulette')
    def get_roulette(self):
        """Возвращает рандомный фильм
        если в списке совподений более 2 фильмов или ошибку"""
        matched_movies = self.get_queryset()
        if len(matched_movies) > 2:
            random_movie = choice(matched_movies)
            serializer = self.serializer_class(random_movie)
            return Response(serializer.data)
        return Response(
            {'error_message': (
                'В списке совподений '
                'должно быть более 2 фильмов.')},
            status=status.HTTP_400_BAD_REQUEST
        )
