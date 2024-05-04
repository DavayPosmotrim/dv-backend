from custom_sessions.models import CustomSession
from movies.models import Genre
from rest_framework import generics

from .serializers import CustomSessionSerializer, GenreSerializer


class GenreListView(generics.ListAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class CustomSessionCreateView(generics.CreateAPIView):
    queryset = CustomSession.objects.all()
    serializer_class = CustomSessionSerializer


class UserSessionListView(generics.ListAPIView):
    serializer_class = CustomSessionSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return CustomSession.objects.filter(users__id=user_id)
