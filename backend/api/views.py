from custom_sessions.models import CustomSession
# from django.db.models import Count
from django.shortcuts import get_object_or_404
from movies.models import Genre, Movie
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from custom_sessions.models import CustomSession
from movies.models import Genre, Movie
from services.schemas import (
    user_schema, user_session_list_schema,
    # genre_list_schema, custom_session_create_schema,
    # movie_list_schema, match_list_schema
)
from users.models import User

from .serializers import (CustomSessionSerializer, CustomUserSerializer,
                          CustomSessionCreateSerializer,
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
    serializer_class = CustomSessionCreateSerializer

    def perform_create(self, serializer):
        session = serializer.save()
        return Response(
            self.get_serializer(session).data,
            status=status.HTTP_201_CREATED
        )


class CustomSessionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CustomSessionSerializer

    def get_queryset(self):
        return CustomSession.objects.all()

    @action(detail=True, methods=['get'])
    def matched_movies(self, request, *args, **kwargs):
        session = self.get_object()
        matched_movies = session.matched_movies
        serializer = MovieSerializer(matched_movies, many=True)
        if matched_movies:
            return Response(serializer.data)
        else:
            return Response({"message": "Нет ни одного совпадения"})

    @action(detail=True, methods=['post'])
    def vote(self, request, *args, **kwargs):
        session = self.get_object()
        movie_ids = [movie.id for movie in session.movies.all()]
        user_ids = [user.id for user in session.users.all()]
        self.notify_vote_update(session, user_ids, movie_ids)
        return Response(status=status.HTTP_201_CREATED)

    def notify_vote_update(self, session, user_ids, movie_ids):
        # логика отправки обновления о голосовании через WebSocket
        # например, с помощью Django Channels
        pass


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
