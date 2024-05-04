from django.urls import path
from .views import GenreListView, CustomSessionCreateView, UserSessionListView


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
]
