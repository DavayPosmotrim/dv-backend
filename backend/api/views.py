from rest_framework import generics

from movies.models import Genre, Movie
from custom_sessions.models import CustomSession
from .serializers import (GenreSerializer, CustomSessionSerializer,
                          MovieSerializer)


class GenreListView(generics.ListAPIView):
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


class MatchListView(generics.ListAPIView):
    """Представление списка избранных фильмов (совпадений)."""

    serializer_class = MovieSerializer

    def get_queryset(self):
        session_id = self.request.session.get('session_id')
        if session_id:
            session = CustomSession.objects.get(id=session_id)
            return session.movies.filter(matched=True)
        return Movie.objects.none()
