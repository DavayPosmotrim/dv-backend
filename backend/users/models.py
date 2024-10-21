from django.db import models
from services.constants import MAX_USER_NAME_LENGTH
from services.validators import validate_name


class User(models.Model):
    """Model for users."""

    name = models.CharField(
        verbose_name="Имя",
        max_length=MAX_USER_NAME_LENGTH,
        validators=[validate_name],
        blank=False,
    )
    device_id = models.UUIDField(
        verbose_name="ID устройства",
        editable=False,
        primary_key=True,
    )

    def __str__(self) -> str:
        return self.name
