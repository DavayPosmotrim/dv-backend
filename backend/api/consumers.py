# api/consumers.py
import json
import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

logger = logging.getLogger(__name__)


class CustomSessionConsumer(WebsocketConsumer):
    def connect(self):
        logger.info("WebSocket connection attempt")
        self.room_name = self.scope["url_route"]["kwargs"]["session_id"]
        self.endpoint = self.scope["url_route"]["kwargs"]["endpoint"]
        self.room_group_name = f"chat_{self.room_name}_{self.endpoint}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()
        logger.info("WebSocket connection established for room: "
                    f"{self.room_group_name}")

    def disconnect(self, close_code):
        logger.info("WebSocket disconnected from room: "
                    f"{self.room_group_name} with code: {close_code}")

        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        logger.info(f"Received WebSocket message: {text_data}")

        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        logger.info(f"Message content: {message}")

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]
        logger.info(f"Sending message to WebSocket: {message}")

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))
