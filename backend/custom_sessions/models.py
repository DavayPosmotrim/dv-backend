from django.contrib.auth import get_user_model
from django.db import models

from movies.models import Movie
# from service.constants import MAX_NAME_LENGTH
from service.counts import generate_id

User = get_user_model()


# class CustomSession(models.Model):
#     """CustomSession model."""
#     name = models.CharField(
#         max_length=125,
#     )

#     class Meta:
#         verbose_name = "CustomSession"
#         verbose_name_plural = "CustomSessions"

#     def __str__(self):
#         return self.name


class Room(models.Model):
    """Модель комнаты/сеанса. """

    # name = models.CharField(
    #     max_length=MAX_NAME_LENGTH,
    # )
    id = models.CharField(
        primary_key=True,
        max_length=8,
        default=generate_id,
        editable=False
    )
    users = models.ManyToManyField(
        User,
        verbose_name='Пользователь',
    )
    movies = models.ManyToManyField(
        Movie,
        verbose_name='Фильм',
    )

    class Meta:
        verbose_name = "Сеанс"
        verbose_name_plural = "Сеансы"

    def __str__(self):
        return self.name
