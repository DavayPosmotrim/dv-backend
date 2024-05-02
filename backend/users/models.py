from api.constants import MAX_DEVICE_ID_LENGTH, MAX_NAME_LENGTH
from api.validators import validate_name
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Model for users."""
    USERNAME_FIELD = "device_id"
    name = models.CharField(
        verbose_name="Имя",
        max_length=MAX_NAME_LENGTH,
        validators=[validate_name],
        blank=False,
    )
    device_id = models.CharField(
        verbose_name="ID устройства",
        max_length=MAX_DEVICE_ID_LENGTH,
        blank=False,
        unique=True,
    )
