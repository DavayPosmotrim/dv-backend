from django.db import models
from services.constants import MAX_MOVIE_NAME_LENGTH


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
        return self.name


class Movie(models.Model):
    """Модель фильма."""

    id = models.IntegerField(
        primary_key=True,
        verbose_name="Уникальный код фильма"
    )
    genres = models.ManyToManyField(
        Genre,
        verbose_name='Жанр',
        blank=True
    )
    name = models.CharField(
        max_length=MAX_MOVIE_NAME_LENGTH,
        verbose_name="Название фильма"
    )
    poster = models.ImageField(
        "Ссылка на изображение",
        upload_to="movies/posters/",
        null=True,
        default=None,
    )
    description = models.TextField(
        verbose_name="Описание фильма",
        null=True,
        blank=True
    )
    year = models.IntegerField(
        verbose_name="Год выпуска",
        null=True,
        blank=True
    )
    countries = models.CharField(
        max_length=255,
        verbose_name="Страны",
        null=True,
        blank=True
    )
    alternative_name = models.CharField(
        max_length=MAX_MOVIE_NAME_LENGTH,
        verbose_name="Альтернативное название",
        null=True,
        blank=True
    )
    rating_kp = models.FloatField(
        verbose_name="Рейтинг Кинопоиск",
        null=True,
        blank=True
    )
    rating_imdb = models.FloatField(
        verbose_name="Рейтинг IMDb",
        null=True,
        blank=True
    )
    movie_length = models.IntegerField(
        verbose_name="Продолжительность фильма (минуты)",
        null=True,
        blank=True
    )
    persons = models.JSONField(
        verbose_name="Персоны",
        null=True,
        blank=True
    )

    class Meta:
        default_related_name = 'movies'
        ordering = ("name",)
        verbose_name = "Фильм"
        verbose_name_plural = "Фильмы"

    def __str__(self):
        return self.name
