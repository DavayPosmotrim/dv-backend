# api/consumers.py
import json
from random import choice

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from custom_sessions.models import CustomSession
from django.shortcuts import get_object_or_404


class CustomSessionConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["session_id"]
        self.room_group_name = f"chat_{self.room_name}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json.get("action")

        if action == "roulette":
            self.handle_roulette()
        elif action == "vote":
            movie_id = text_data_json.get("movie_id")
            device_id = self.scope["headers"].get("device_id")
            self.handle_vote(movie_id, device_id)

    def handle_roulette(self):
        current_session = get_object_or_404(CustomSession, id=self.room_name)
        matched_movies = current_session.matched_movies.all()
        if matched_movies.count() > 2:
            # change session status to closed
            current_session.status = "closed"
            current_session.save()
            random_movie_id = choice(list(matched_movies)).movie_id
            self.broadcast_message(random_movie_id)

    def handle_vote(self, movie_id, device_id):
        pass

    def broadcast_message(self, message):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))
