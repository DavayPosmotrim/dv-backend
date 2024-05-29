from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from .views import (CreateUpdateUserView, CustomSessionCreateView,
                    CustomSessionViewSet, GenreListView, MovieListView,
                    UserMovieVoteCreateView, UserSessionListView,
                    UserVoteListView)

router = DefaultRouter()
# router.register(
#     r'matches/(?P<session_id>\w+)', CustomSessionViewSet, basename='match'
# )
router.register(
    r'custom_sessions', CustomSessionViewSet, basename='custom_session'
)

urlpatterns = [
    path('', include(router.urls)),
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
    path(
        'votes/<str:session_id>/<int:user_id>/',
        UserMovieVoteCreateView.as_view(),
        name='votes_create'),
    path(
        'votes/<str:session_id>/',
        UserVoteListView.as_view({'get': 'list'}),
        name='votes_list'),
    path('movies/', MovieListView.as_view(), name='movie_list'),
    # path('matches/', MatchListView.as_view(), name='match_list'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
]
