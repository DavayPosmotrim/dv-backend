from django.urls import path

from .views import (CreateUpdateUserView, CustomSessionCreateView,
                    GenreListView, MatchListView, MovieListView,
                    UserSessionListView)

urlpatterns = [
    path('v1/users/',
         CreateUpdateUserView.as_view(),
         name='create_update_user'),
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
