"""Служебные функции . """

from api.serializers import CustomSessionSerializer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def format_date(date):
    # возвращает дату сеанса в отформатированном виде
    months = [
        "января",
        "февраля",
        "марта",
        "апреля",
        "мая",
        "июня",
        "июля",
        "августа",
        "сентября",
        "октября",
        "ноября",
        "декабря",
    ]
    day = date.day
    month = months[date.month - 1]
    year = date.year

    return f"{day} {month} {year}"


def send_websocket_message(session_id, endpoint, message):
    """Send message to room_group_name on websocket."""
    channel_layer = get_channel_layer()
    room_group_name = "_".join(["chat", session_id, endpoint])
    async_to_sync(channel_layer.group_send)(
        room_group_name,
        {
            "type": "chat.message",
            "message": message,
        }
    )


def close_session(session, session_id, send_status=True) -> None:
    new_status = "closed"
    session.status = new_status
    session.save()
    if session.matched_movies.exists():
        serializer = CustomSessionSerializer(session)
        send_websocket_message(session_id, "session_result", serializer.data)
    if send_status:
        send_websocket_message(session_id, "session_status", new_status)
