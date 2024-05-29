from custom_sessions.models import CustomSession, UserMovieVote
from movies.models import Genre, Movie
from rest_framework import serializers
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
        fields = ['movie']

    def create(self, validated_data):
        user_id = self.context['view'].kwargs['user_id']
        session_id = self.context['view'].kwargs['session_id']
        user = User.objects.get(pk=user_id)
        session = CustomSession.objects.get(pk=session_id)
        return UserMovieVote.objects.create(
            user=user,
            movie_id=validated_data['movie'],
            session=session
        )

    def to_representation(self, instance):
        return {
            'user': instance.user.id,
            'movie': instance.movie.id,
            'session': instance.session.id
        }

    # def update_custom_session(self, custom_session):
    #     custom_session.refresh_from_db()
    #     return custom_session


class CustomSessionCreateSerializer(serializers.ModelSerializer):
    movies = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Movie.objects.all()
    )
    users = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all()
    )
    id = serializers.CharField(read_only=True)

    class Meta:
        model = CustomSession
        fields = ['id', 'movies', 'date', 'status', 'users']

    def create(self, validated_data):
        movies = validated_data.pop('movies')
        users = validated_data.pop('users')
        session = CustomSession.objects.create(**validated_data)
        session.movies.set(movies)
        session.users.set(users)
        return session


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

    # def to_representation(self, instance):
    #     """Принимает экземпляр модели сессии.
    #        Определяет список фильмов, за которые проголосовали
    #        все пользователи в данной сессии.
    #        Добавляет этот список в поле 'matched_movies'.
    #        Возвращает в виде словаря представление экземпляра CustomSession,
    #        включая поле 'matched_movies'."""
    #     representation = super().to_representation(instance)
    #     votes = UserMovieVote.objects.filter(session=instance)
    #     user_ids = list(instance.users.values_list('id', flat=True))
    #     movie_ids = votes.values_list('movie_id', flat=True).distinct()
    #     matched_movies = []
    #     for movie_id in movie_ids:
    #         if votes.filter(movie_id=movie_id).count() == len(user_ids):
    #             matched_movies.append(Movie.objects.get(id=movie_id))

    #     representation['matched_movies'] = matched_movies
    #     return representation
