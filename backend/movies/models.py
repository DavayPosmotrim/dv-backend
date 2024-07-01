from django.contrib.postgres.fields import ArrayField
from django.db import models
from services.constants import MAX_MOVIE_NAME_LENGTH, MAX_NAME_LENGTH


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


class Collection(models.Model):
    """Модель подборки."""

    name = models.CharField(
        "Название подборки",
        max_length=MAX_MOVIE_NAME_LENGTH,
    )
    slug = models.SlugField(
        unique=True,
        null=False,
        blank=False
    )
    cover = models.ImageField(
        "Ссылка на изображение",
        upload_to="collections/",
        null=True,
        default=None
    )

    class Meta:
        verbose_name = "Подборка"
        verbose_name_plural = "Подборка"
        ordering = ("name",)


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
    countries = ArrayField(
        models.CharField(max_length=MAX_NAME_LENGTH),
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
    votes_kp = models.IntegerField(
        verbose_name="Голоса Кинопоиск",
        null=True,
        blank=True
    )
    votes_imdb = models.IntegerField(
        verbose_name="Голоса IMDb",
        null=True,
        blank=True
    )
    movie_length = models.IntegerField(
        verbose_name="Продолжительность фильма (минуты)",
        null=True,
        blank=True
    )
    actors = ArrayField(
        models.CharField(max_length=MAX_NAME_LENGTH),
        verbose_name="Актеры",
        null=True,
        blank=True,
        size=4
    )
    directors = ArrayField(
        models.CharField(max_length=MAX_NAME_LENGTH),
        verbose_name="Режиссеры",
        null=True,
        blank=True,
        size=4
    )

    class Meta:
        default_related_name = 'movies'
        ordering = ("name",)
        verbose_name = "Фильм"
        verbose_name_plural = "Фильмы"

    def __str__(self):
        return self.name
