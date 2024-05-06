from django.urls import path

from .views import (CustomSessionCreateView, GenreListView, MatchListView,
                    MovieListView, UserSessionListView)

urlpatterns = [
    path('genres/', GenreListView.as_view(), name='genre-list'),
    path(
        'sessions/create/',
        CustomSessionCreateView.as_view(),
        name='session_create'
    ),
    path(
        'sessions/<int:user_id>/',
        UserSessionListView.as_view(),
        name='user_sessions'
    ),
    path('movies/', MovieListView.as_view(), name='movie_list'),
    path('matches/', MatchListView.as_view(), name='match_list'),
]
