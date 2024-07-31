"""Служебные функции . """

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


def get_session_image(session):
    if session.status == 'closed':
        matched_movies = list(session.matched_movies)
        if matched_movies:
            top_movie = max(
                matched_movies, key=lambda movie: movie.rating_kp
            )
            if top_movie and top_movie.poster:
                session.image = top_movie.poster
                session.save()
