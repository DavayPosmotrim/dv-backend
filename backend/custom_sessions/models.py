import random
import string

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
        blank=True,
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
    matched_movies = models.ManyToManyField(
        Movie,
        blank=True,
        related_name='matched_movies_custom_sessions',
        verbose_name='Избранный фильм',
    )

    class Meta:
        ordering = ("date",)
        default_related_name = 'custom_sessions'
        verbose_name = "Сеанс"
        verbose_name_plural = "Сеансы"

    def __str__(self):
        return f"CustomSession {self.id or 'Unknown'}"

    def get_formatted_date(self):
        if self.date:
            return format_date(self.date)
        else:
            return 'Дата не установлена'


class CustomSessionMovieVote(models.Model):
    """Model for movie votes within session."""
    session_id = models.ForeignKey(
        CustomSession,
        related_name="votes",
        on_delete=models.CASCADE,
    )
    user_id = models.ForeignKey(
        User,
        related_name="votes",
        on_delete=models.CASCADE
    )
    movie_id = models.ForeignKey(
        Movie,
        related_name="votes",
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "CustomSessionMovieVote"
        verbose_name_plural = "CustomSessionMovieVotes"
        constraints = [
            models.UniqueConstraint(
                fields=["session_id", "user_id", "movie_id"],
                name='unique_vote'
            )
        ]
