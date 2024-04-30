import uuid
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import UniqueConstraint

from service.constants import MAX_NAME_LENGTH


User = get_user_model()


class Genre(models.Model):
    """Модель жанра."""

    name = models.CharField(
        "Название жанра",
        max_length=MAX_NAME_LENGTH,
    )

    class Meta:
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"
        ordering = ("name",)

    def __str__(self):
        return self.title


class Movie(models.Model):
    """Модель фильма."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Уникальный код фильма"
    )
    genre = models.ManyToManyField(
        Genre,
        verbose_name='Жанр',
        blank=True
    )
    name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name="Название фильма"
    )

    # name_original = models.CharField(
    #     max_length=50,
    #     verbose_name="Оригинальное название фильма"
    # )
    # image = models.ImageField(
    #     "Ссылка на изображение",
    #     upload_to="movies/images/",
    #     null=True,
    #     default=None,
    # )
    # description = models.TextField(
    #     "Описание",
    # )
    # year = models.PositiveSmallIntegerField(
    #     verbose_name="Год выпуска",
    #     validators=[
    #         MinValueValidator(1900),
    #         MaxValueValidator(date.today().year)
    #     ]
    # )
    # countries
    # duration

    class Meta:
        default_related_name = 'movies'
        ordering = ("name",)
        verbose_name = "Фильм"
        verbose_name_plural = "Фильмы"

    def __str__(self):
        return self.name


class GenreTitle(models.Model):
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


class Favorite(models.Model):
    """Модель избранных фильмов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
    )

    class Meta:
        default_related_name = "favorites"
        ordering = ("movie",)
        verbose_name = "Избранное"
        constraints = [
            UniqueConstraint(
                fields=["user", "movie"],
                name="unique_favorite"
            )
        ]
