from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CreateUpdateUserView, CustomSessionCreateView,
                    GenreListView, MatchViewSet, MovieListView,
                    UserSessionListView)

router_api_v1 = DefaultRouter()

router_api_v1.register(r'^matches',
                       MatchViewSet,
                       basename='matches')


urlpatterns = [
    path('v1/', include(router_api_v1.urls)),
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

]
