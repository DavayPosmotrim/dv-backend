from django.urls import path

from .views import CreateUpdateUserView

urlpatterns = [
    path('v1/users/',
         CreateUpdateUserView.as_view(),
         name='create_update_user'),
]
