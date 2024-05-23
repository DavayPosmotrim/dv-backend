from rest_framework import serializers

from custom_sessions.models import CustomSession, UserMovieVote
from movies.models import Genre, Movie
from users.models import User


class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer for user."""

    class Meta:
        model = User
        fields = ('name', 'device_id')
        extra_kwargs = {
            'device_id': {'write_only': True},  # Hide device_id from responses
        }


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор жанра."""

    class Meta:
        model = Genre
        fields = [
            'id',
            'name'
        ]


class MovieSerializer(serializers.ModelSerializer):
    """Сериализатор фильма/списка фильмов."""

    genre = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Genre.objects.all()
    )

    class Meta:
        model = Movie
        fields = ['id', 'name', 'genre', 'image']


class UserMovieVoteSerializer(serializers.ModelSerializer):
    """Сериализатор голоса пользователя к фильму."""

    class Meta:
        model = UserMovieVote
        fields = ['user', 'movie', 'session']


class CustomSessionSerializer(serializers.ModelSerializer):
    """Сериализатор сеанса/комнаты."""

    users = CustomUserSerializer(many=True, read_only=True)
    movie_votes = UserMovieVoteSerializer(
        many=True, source='usermovievote_set', read_only=True
    )
    matched_movies = MovieSerializer(many=True, read_only=True)

    class Meta:
        model = CustomSession
        fields = [
            'id',
            'users',
            'movies',
            'date',
            'status',
            'movie_votes',
            'matched_movies',
        ]

    def to_representation(self, instance):
        """Принимает экземпляр модели сессии.
           Определяет список фильмов, за которые проголосовали
           все пользователи в данной сессии.
           Добавляет этот список в поле 'matched_movies'.
           Возвращает в виде словаря представление экземпляра CustomSession,
           включая поле 'matched_movies'."""
        representation = super().to_representation(instance)
        num_users_in_session = instance.users.count()
        votes = UserMovieVote.objects.filter(session=instance)
        movies_voted = [vote.movie.id for vote in votes]
        matched_movies_queryset = [
            movie for movie in instance.movies.all()
            if movies_voted.count(movie.id) == num_users_in_session
        ]
        matched_movies_field = self.get_fields()['matched_movies']
        representation[
            'matched_movies'
        ] = matched_movies_field.to_representation(matched_movies_queryset)
        return representation
