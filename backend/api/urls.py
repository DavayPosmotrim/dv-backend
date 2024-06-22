from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from .views import (
    # CreateUpdateUserView,
    CustomSessionViewSet, GenreListView,
    MovieListView, MovieDetailView
)

router = DefaultRouter()
router.register(
    r'sessions', CustomSessionViewSet, basename='sessions'
)

urlpatterns = [
    path('', include(router.urls)),
    # path('v1/users/',
    #      CreateUpdateUserView.as_view(),
    #      name='create_update_user'),

    path('genres/', GenreListView.as_view(), name='genre_list'),
    path('movies/', MovieListView.as_view(), name='movie_list'),
    path(
        'movies/<int:movie_id>/',
        MovieDetailView.as_view(), name='movie_detail'
    ),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
]
