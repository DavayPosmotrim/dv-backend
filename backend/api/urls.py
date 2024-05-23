from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .views import (
    CreateUpdateUserView,
    CustomSessionCreateView,
    GenreListView,
    UserSessionListView,
    MovieListView,
    MatchListView
)

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
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
]
