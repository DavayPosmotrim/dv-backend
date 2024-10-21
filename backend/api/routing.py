# chat/routing.py
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(
        r"ws/session/(?P<session_id>\w+)/(?P<endpoint>\w+)/$",
        consumers.CustomSessionConsumer.as_asgi(),
    ),
]
