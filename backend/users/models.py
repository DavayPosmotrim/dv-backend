from django.contrib.auth.models import AbstractUser
from django.db import models
from services.constants import MAX_DEVICE_ID_LENGTH, MAX_USER_NAME_LENGTH
from services.validators import validate_name


class User(AbstractUser):
    """Model for users."""
    USERNAME_FIELD = "device_id"
    name = models.CharField(
        verbose_name="Имя",
        max_length=MAX_USER_NAME_LENGTH,
        validators=[validate_name],
        blank=False,
    )
    device_id = models.CharField(
        verbose_name="ID устройства",
        max_length=MAX_DEVICE_ID_LENGTH,
        blank=False,
        unique=True,
    )
