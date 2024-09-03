"""Константы, используемые в моделях и api. """

MAX_USER_NAME_LENGTH: int = 16
MAX_DEVICE_ID_LENGTH: int = 36
MAX_MOVIE_NAME_LENGTH = 250
MAX_PERSON_NAME_LENGTH = 250
MAX_COLLECTION_NAME_LENGTH = 250
MAX_GENRE_NAME_LENGTH = 50
MAX_NAME_LENGTH = 250

STATUS_CHOICES = [
    ("waiting", "Ожидание"),
    ("voting", "Голосование"),
    ("closed", "Закрыто"),
]

MAX_MOVIES_QUANTITY = 500
