"""Константы, используемые в моделях и api. """

MAX_USER_NAME_LENGTH: int = 16
MAX_DEVICE_ID_LENGTH: int = 24
MAX_MOVIE_NAME_LENGTH = 50

STATUS_CHOICES = [
    ('waiting', 'Ожидание'),
    ('voting', 'Голосование'),
    ('closed', 'Закрыто'),
]
