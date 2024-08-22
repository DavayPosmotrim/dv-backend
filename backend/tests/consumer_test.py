import os

import pytest
from api.consumers import CustomSessionConsumer
from channels.layers import get_channel_layer
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.urls import path

# Ensure the Django settings are loaded
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')


async def send_websocket_message(session_id, endpoint, message):
    """Send message to room_group_name on websocket."""
    channel_layer = get_channel_layer()
    room_group_name = "_".join(["chat", session_id, endpoint])
    await channel_layer.group_send(
        room_group_name,
        {
            "type": "chat.message",
            "message": message,
        }
    )


@pytest.mark.asyncio
async def test_custom_session_consumer():
    # Setup the application with the consumer
    test_application = URLRouter([
        path("ws/session/<session_id>/<endpoint>/", CustomSessionConsumer.as_asgi()),
    ])
    session_id = "abc123"
    endopoint = "data"

    # Create a communicator connected to your consumer
    communicator = WebsocketCommunicator(test_application, f"/ws/session/{session_id}/{endopoint}/")
    connected, _ = await communicator.connect()
    assert connected

    # Test sending a message
    await send_websocket_message(session_id, endopoint, message="hello")
    response = await communicator.receive_from()
    assert response == '{"message": "hello"}'

    # Close the WebSocket
    await communicator.disconnect()
