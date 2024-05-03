from django.db import models
from service.constants import MAX_MOVIE_NAME_LENGTH


class User(models.Model):
    """Заглушка. """

    name = models.CharField(
        verbose_name="Имя"
    )
    device_id = models.CharField(
        verbose_name="ID устройства"
    )


class Genre(models.Model):
    """Модель жанра."""

    name = models.CharField(
        "Название жанра",
        max_length=MAX_MOVIE_NAME_LENGTH,
    )

    class Meta:
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"
        ordering = ("name",)

    def __str__(self):
        return self.title


class Movie(models.Model):
    """Модель фильма."""

    id = models.IntegerField(
        primary_key=True,
        verbose_name="Уникальный код фильма"
    )
    genre = models.ManyToManyField(
        Genre,
        verbose_name='Жанр',
        blank=True
    )
    name = models.CharField(
        max_length=MAX_MOVIE_NAME_LENGTH,
        verbose_name="Название фильма"
    )

    class Meta:
        default_related_name = 'movies'
        ordering = ("name",)
        verbose_name = "Фильм"
        verbose_name_plural = "Фильмы"

    def __str__(self):
        return self.name


class GenreMovie(models.Model):
    """Вспомогательная модель, связывает произведения и жанры."""

    genre = models.ForeignKey(
        Genre,
        verbose_name='Жанр',
        on_delete=models.CASCADE
    )
    movie = models.ForeignKey(
        Movie,
        verbose_name='Фильм',
        on_delete=models.CASCADE
    )

    class Meta:
        default_related_name = 'genresmovies'
