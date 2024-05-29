import string
import random

from django.db import models
from movies.models import Movie
from services.constants import STATUS_CHOICES
from services.utils import format_date
from users.models import User


def generate_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))


class CustomSession(models.Model):
    """Модель комнаты/сеанса. """

    id = models.CharField(
        primary_key=True,
        default=generate_id,
        max_length=8,
        editable=False,
        verbose_name="Уникальный идентификатор сессии"
    )
    users = models.ManyToManyField(
        User,
        verbose_name='Пользователь',
    )
    movies = models.ManyToManyField(
        Movie,
        verbose_name='Фильм',
    )
    date = models.DateField(
        verbose_name='Дата',
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
    )

    class Meta:
        ordering = ("date",)
        verbose_name = "Сеанс"
        verbose_name_plural = "Сеансы"

    def __str__(self):
        return f"CustomSession {self.id or 'Unknown'}"

    def get_formatted_date(self):
        if self.date:
            return format_date(self.date)
        else:
            return 'Дата не установлена'


class UserMovieVote(models.Model):
    """Модель голоса пользователя за фильм в рамках сессии. """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE
    )
    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE
    )
    session = models.ForeignKey(
        CustomSession, on_delete=models.CASCADE
    )

    class Meta:
        ordering = ("movie",)
        verbose_name = "Голос"
        verbose_name_plural = "Голоса"

    def __str__(self):
        return f"{self.user} - {str(self.movie)}"
