from django.db import models


class CustomSession(models.Model):
    """CustomSession model."""
    name = models.CharField(
        max_length=125,
    )

    class Meta:
        verbose_name = "CustomSession"
        verbose_name_plural = "CustomSessions"

    def __str__(self):
        return self.name


class Room(models.Model):
    """Модель комнаты/сеанса. """

    name = models.CharField(
        max_length=125,
    )

    class Meta:
        verbose_name = "CustomSession"
        verbose_name_plural = "CustomSessions"

    def __str__(self):
        return self.name