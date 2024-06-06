from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from .views import (CreateUpdateUserView, CustomSessionCreateView,
<<<<<<< HEAD
                    GenreListView, CustomSessionViewSet, MovieListView)
=======
                    CustomSessionViewSet, GenreListView, MovieListView,
                    UserSessionListView)
>>>>>>> ccc5b9288a298a380235f7990a04a62384e5149f

router = DefaultRouter()
router.register(
    r'users/(?P<device_id>\d+)/sessions/',
    CustomSessionViewSet, basename='custom_session'
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
    path('movies/', MovieListView.as_view(), name='movie_list'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
]
