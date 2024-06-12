from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .views import (CreateUpdateUserView, CustomSessionCreateView,
                    CustomSessionViewSet, GenreListView, MovieListView)


urlpatterns = [
    path('v1/users/',
         CreateUpdateUserView.as_view(),
         name='create_update_user'),
    path('genres/', GenreListView.as_view(), name='genre-list'),
    path('movies/', MovieListView.as_view(), name='movie_list'),
    path(
        'sessions/create/',
        CustomSessionCreateView.as_view(),
        name='session_create'
    ),
    path('sessions/<int:session_id>/',
         CustomSessionViewSet.as_view({'get': 'retrieve'}),
         name='session_detail'),
    path('sessions/<int:session_id>/matched_movies/',
         CustomSessionViewSet.as_view({'get': 'matched_movies'}),
         name='session_matched_movies'),
    path('sessions/<int:session_id>/get_roulette/',
         CustomSessionViewSet.as_view({'get': 'get_roulette'}),
         name='session_roulette'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
]
