from custom_sessions.models import CustomSession
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from custom_sessions.models import CustomSession
from movies.models import Genre, Movie
from services.schemas import (
    user_schema, match_list_schema, user_session_list_schema,
    # genre_list_schema, custom_session_create_schema,
    # movie_list_schema, match_list_schema
)
from users.models import User

from .serializers import (CustomSessionSerializer, CustomUserSerializer,
                          GenreSerializer, MovieSerializer)


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


class CustomSessionCreateView(generics.CreateAPIView):
    """Создание пользовательского сеанса."""

    queryset = CustomSession.objects.all()
    serializer_class = CustomSessionSerializer


class UserSessionListView(generics.ListAPIView):
    """Представление списка сеансов пользователя."""

    serializer_class = CustomSessionSerializer

    @user_session_list_schema['get']
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return CustomSession.objects.filter(users__id=user_id)


class MovieListView(generics.ListAPIView):
    """Представление списка фильмов."""

    queryset = Movie.objects.all()
    serializer_class = MovieSerializer


class MatchListView(viewsets.ModelViewSet):
    """Представление списка избранных фильмов (совпадений)."""

    serializer_class = MovieSerializer

    @match_list_schema['get']
    def get_queryset(self):
        session_id = self.request.session.get('session_id')
        session = get_object_or_404(CustomSession, id=session_id)
        return session.matched_movies.all()
