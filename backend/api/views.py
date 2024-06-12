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

from .serializers import (ClosedSessionSerializer,
                          CustomSessionCreateSerializer, CustomUserSerializer,
                          DraftSessionSerializer,
                          GenreSerializer, MovieSerializer,
                          VotingSessionSerializer, WaitingSessionSerializer)


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
    """Создание пользовательского сеанса
    при переходе в статус voting."""

    queryset = CustomSession.objects.all()
    serializer_class = CustomSessionCreateSerializer

    def perform_create(self, serializer):
        session = serializer.save()
        return Response(
            self.get_serializer(session).data,
            status=status.HTTP_201_CREATED
        )


class CustomSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление текущей сессии для пользователя
    и списка закрытых сессий пользователя
    с возможностью посмотреть их детали."""

    def get_serializer_class(self):
        """Разделяет сериализаторы для закрытых(архивных) сессий
        и текущих. Для текущих сессий разделяет сериализаторы
        в зависимости от статуса сессии ."""
        if 'session_id' in self.kwargs:
            status = self.get_object().status
            if status == 'draft':
                return DraftSessionSerializer
            elif status == 'waiting':
                return WaitingSessionSerializer
            elif status == 'voting':
                return VotingSessionSerializer
            else:
                return ClosedSessionSerializer
        else:
            return ClosedSessionSerializer

    def get_queryset(self):
        device_id = self.request.headers.get('device_id')
        if device_id:
            return CustomSession.objects.filter(
                users__device_id=device_id
            )
        else:
            return CustomSession.objects.none()

    @action(detail=True, methods=['get'])
    def matched_movies(self, request, pk=None, *args, **kwargs):
        """Возвращает фильмы, за которые проголосовали все пользователи
        в сесиии (мэтчи) - или ошибку, если мэтчей нет ."""
        session = self.get_object()
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

    @user_session_list_schema['get']
    @action(detail=True, methods=['get'])
    def get_closed_sessions(self, request, *args, **kwargs):
        """Возвращает все закрытые сессии текущего пользователя,
         в которых были мэтчи, или сообщение об отсутствии таковых."""
        closed_sessions = self.get_queryset().filter(
            status='closed', matched_movies__isnull=False
        )
        if closed_sessions.exists():
            serializer = self.get_serializer(closed_sessions, many=True)
            return Response(serializer.data)
        else:
            return Response(
                {"message": "Нет ни одной закрытой сессии с мэтчами"}
            )


class MovieListView(generics.ListAPIView):
    """Представление списка фильмов."""

    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
