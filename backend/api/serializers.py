from rest_framework import serializers

from movies.models import Genre
from custom_sessions.models import CustomSession


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = [
            'id',
            'name'
        ]


class CustomSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomSession
        fields = [
            'id',
            'users',
            'movies',
            'date',
            'status'
        ]
