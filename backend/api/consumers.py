# api/consumers.py
import json
import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

logger = logging.getLogger(__name__)


class CustomSessionConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["session_id"]
        self.endpoint = self.scope["url_route"]["kwargs"]["endpoint"]
        self.room_group_name = f"chat_{self.room_name}_{self.endpoint}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    # Новый метод для обработки сообщений типа 'users'
    def users(self, event):
        data = event['data']

        # Отправляем сообщение клиенту по веб-сокету
        self.send(text_data=json.dumps({
            'type': 'users',
            'data': data
        }))

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]
        # Проверяем, является ли сообщение списком пользователей
        if isinstance(message, dict) and message.get('type') == 'users':
            # Отправляем список пользователей клиенту
            self.send(text_data=json.dumps({
                'type': 'users',
                'data': message.get('data')
            }))
        else:
            # Отправляем обычное сообщение клиенту
            self.send(text_data=json.dumps({"message": message}))
